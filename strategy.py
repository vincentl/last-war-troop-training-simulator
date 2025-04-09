import re
import heapq
import plotly.express as px
import pandas as pd
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass(order=True)
class Barrack:
    level: int
    capacity: int
    index: int | None = None

@dataclass
class BaseTrainRate:
    level: int
    capacity: int
    duration: str

@dataclass
class BasePromoteRate:
    capacity: int
    duration: str

@dataclass(order=True)
class Activity:
    finish: float
    start: float
    description: str
    resource: Barrack
    count: int
    level: int
    duration: float

def parse_duration(duration_str):
    pattern = r'(?:(\d+)d)?\s*(\d{1,2}):(\d{2}):(\d{2})'
    match = re.match(pattern, duration_str.strip())
    if not match:
        raise ValueError("Invalid format. Expected something like '1d 07:45:09'")

    days = int(match.group(1)) if match.group(1) else 0
    hours = int(match.group(2))
    minutes = int(match.group(3))
    seconds = int(match.group(4))

    total_seconds = days * 86400 + hours * 3600 + minutes * 60 + seconds
    return total_seconds

def seconds_to_duration(seconds):
    seconds = round(seconds)
    days = seconds // 86400
    remainder = seconds % 86400
    hours = remainder // 3600
    minutes = (remainder % 3600) // 60
    secs = remainder % 60
    return f'{days}d {hours:02}:{minutes:02}:{secs:02}'

# Train Example
# 5 712 19:03:47
# 6 712 22:14:25
# 7 712 1d 01:25:03
# 8 712 1d 04:35:40
# 9 712 1d 07:46:18

# Promote Example
# 5 -> 6 561 02:27:50
# 6 -> 7 589 02:35:13
# 7 -> 8 647 02:50:30
# 8 -> 9 723 03:10:31

def simulate(barracks: list[Barrack],
             base_train_rate: BaseTrainRate,
             base_promote_rate: BasePromoteRate,
             goal: int,
             strategy: str) -> (str, pd.DataFrame):
    # Derive other rates
    max_level = max(b.level for b in barracks)
    train_rates = {base_train_rate.level: parse_duration(base_train_rate.duration) / base_train_rate.capacity}
    for level in range(base_train_rate.level, max_level):
        train_rates[level + 1] = train_rates[level] * (level + 2.0)/(level + 1.0)
    for level in range(base_train_rate.level, 1, -1):
        train_rates[level - 1] = train_rates[level] * level/(level + 1.0)
    promote_rate = parse_duration(base_promote_rate.duration) / float(base_promote_rate.capacity)

    # Setup a few closures
    base_time = datetime.now()
    def seconds_to_sim_time(seconds: float) -> datetime:
        return base_time + timedelta(seconds=seconds)
    def promote(count: int, levels: int) -> float:
        return count * levels * promote_rate
    def train(count: int, level: int) -> float:
        return train_rates[level] * count
    def activity_to_frame(activity: Activity) -> dict[str, str | float]:
        return {
            'Barrack': f'Barrack {activity.resource.index}',
            'Start': seconds_to_sim_time(activity.start),
            'Finish': seconds_to_sim_time(activity.finish),
            'Start@': seconds_to_duration(activity.start),
            'Finish@': seconds_to_duration(activity.finish),
            'Task': activity.description,
            'Type': 'Promote' if 'promote' in activity.description else 'Train',
            'Duration': activity.duration
        }

    # base level pipeline - order barracks by level 
    #   if there are at least capacity troops at a level below max, promote to max
    #   else if there are troops to start, train @ 1 level below lowest level
    #   else if there are any troops at a level below max, train to max
    #   else idle 
    # max level pipeline - order barracks by level 
    #   if there are at least capacity troops at a level below max, promote to max
    #   else if there are troops to start, train @ max level
    #   else if there are any troops at a level below max, train to max
    #   else idle

    barracks = list(sorted([b for b in barracks if b.capacity > 0]))
    min_level = barracks[0].level

    idle: list[Barrack] = []
    for index, barrack in enumerate(barracks):
        barrack.index = index
        heapq.heappush(idle, barrack)

    pipeline = [0] * (1 + max_level)
    pipeline[0] = goal
    inflight: list[Activity] = []
    frames: list[dict[str, str | float]] = []

    now = 0
    while pipeline[-1] != goal:
        print(pipeline)
        # I. retire completed activity
        if len(inflight):
            activity = heapq.heappop(inflight)
            print('Finish', activity)
            pipeline[activity.level] += activity.count
            now = activity.finish
            heapq.heappush(idle, activity.resource)
        # II. schedule idle nodes
        skip: list[Barrack] = []
        while len(idle):
            barrack = heapq.heappop(idle)
            if promote_from := next((level for level in range(1, barrack.level) if pipeline[level] >= barrack.capacity), None):
                # 1. if there are at least capacity troops at a level below max, promote to max
                count = barrack.capacity
                pipeline[promote_from] -= count
                cost = promote(count, barrack.level - promote_from)
                description = f'Barracks {barrack.index} - promote {count} troops from level {promote_from} to level {barrack.level} at cost {seconds_to_duration(cost)}'
                activity = Activity(now + cost, now, description, barrack, count, barrack.level, cost)
                print('Start', activity)
                frames += [activity_to_frame(activity)]
                heapq.heappush(inflight, activity)
            elif pipeline[0] > 0:
                # 2. else if there are troops to start, train either at start level
                count = min(pipeline[0], barrack.capacity)
                pipeline[0] -= count
                match strategy:
                    case 'min - 1':
                        target_level = min_level - 1
                    case 'max level':
                        target_level = barrack.level
                cost = train(count, target_level)
                description = f'Barracks {barrack.index} - train {count} troops at level {target_level} at cost {seconds_to_duration(cost)}'
                activity = Activity(now + cost, now, description, barrack, count, target_level, cost)
                print('Start', activity)
                frames += [activity_to_frame(activity)]
                heapq.heappush(inflight, activity)
            elif promote_from := next((level for level in range(1, barrack.level) if pipeline[level] > 0), None):
                # 3. else if there are any troops at a level below max, train to max
                count = pipeline[promote_from]
                pipeline[promote_from] -= count
                cost = promote(count, barrack.level - promote_from)
                description = f'Barracks {barrack.index} - promote {count} troops from level {promote_from} to level {barrack.level} at cost {seconds_to_duration(cost)}'
                activity = Activity(now + cost, now, description, barrack, count, barrack.level, cost)
                print('Start', activity)
                frames += [activity_to_frame(activity)]
                heapq.heappush(inflight, activity)
            else:
                # 4. idle
                heapq.heappush(skip, barrack)
        idle = skip
    total_barrack_time = sum(row['Duration'] for row in frames)
    print(frames)
    return seconds_to_duration(now), pd.DataFrame(frames), seconds_to_duration(total_barrack_time)
