from anytree import Node, RenderTree
import re
import pandas as pd
import calendar
import copy

from collections.abc import Mapping


def parse_time_string(s):

    parser = re.compile(r"^(?:(?P<season_epoch>e|m|l)?(?P<season>(Winter|Spring|Summer|Autumn)) +)?(?P<fuzzy>~)?(?P<year_epoch>e|m|l)?(?P<year>(/?-?\d+s?)+)(?:\.(?P<month_epoch>e|m|l)?(?P<month>(/?\d\d)+))?(?:\.(?P<day>(/?\d\d)+))?$", re.IGNORECASE) # noqa
    
    match = parser.search(s.strip())

    if match is None:
        raise RuntimeError(f"Could not parse time string '{s}'.")
    
    d = match.groupdict()

    
    for key in list(d.keys()):
        
        value = d[key]
        if value is None:
            d.pop(key)
            continue
    
        if key in ["fuzzy", "period"]:
            value = True
    
        if "epoch" in key:
            value = {"e": "early", "m": "mid", "l": "late"}[value]

        # value = [str(s).lower() for s in value.split("/")]
    
        if key == "month":
            value = "/".join([calendar.month_name[int(v)].lower() for v in value.split("/")])
    
        if isinstance(value, str):
            value = value.lower()
            
        d[key] = value

    return d

class Time():
    """
    This can be a specific date, but it can also be things like:
    - December 1960
    - Late Spring, 1923
    - 1686
    - July/August 1987 (like for a magazine issue)
    """

    fields = {
              "year": str, 
              "year_epoch": str, 
              "season": str, 
              "season_epoch": str, 
              "month": str, 
              "month_epoch": str, 
              "day": int, 
              "holiday": str, 
              "fuzzy": bool, 
            }

    def __init__(self, t):

        if not isinstance(t, Mapping):
            t = parse_time_string(str(t))

        self.tree = self.empty_tree()

        for k, v in t.items(): 
            for sibling in self.tree[k]["node"].siblings:
                sibling_value = self.tree[sibling.name].get("value")
                if sibling_value is not None:
                    raise ValueError(f"Redundancy: {k}={v} and {sibling.name}={sibling_value}.")
        
            self.tree[k]["value"] = v

        for k, v in self.tree.items():
            if v.get("value") is not None:
                parent = v["node"].parent
                if parent is not None:
                    parent_value = self.tree[parent.name].get("value")
                    if parent_value is None:
                        raise ValueError(f"Orphan: {k}={v['value']} but {parent.name}={parent_value}.")
                    if parent_value is list:
                        raise ValueError(f"Overspecified: {k}={v['value']} but {parent.name}={parent_value}.")


    def __getattr__(self, attr):
        if attr in self.tree:
            return self.tree[attr].get("value")
        else:
            raise KeyError(f"No attribute '{attr}'.")


    @property
    def numerical_year(self):
        return int(self.year.strip("s"))

    @property
    def era(self):
        return "AD" if self.numerical_year > 0 else "BC"
    
    @classmethod
    def from_dict(cls, d):
        return cls(**d)

    @staticmethod
    def empty_tree():
        
        tree = {}

        tree["fuzzy"] = {"node": Node("fuzzy")}
        # tree["period"] = {"node": Node("period")}
        tree["year"] = {"node": Node("year")}
        tree["holiday"] = {"node": Node("holiday", parent=tree["year"]["node"])}
        tree["month"] = {"node": Node("month", parent=tree["year"]["node"])}
        tree["season"] = {"node": Node("season", parent=tree["year"]["node"])}
        tree["day"] = {"node": Node("day", parent=tree["month"]["node"])}
        tree["weekday"] = {"node": Node("weekday", parent=tree["day"]["node"])}
        
        tree["year_epoch"] = {"node": Node("year_epoch", parent=tree["year"]["node"])}
        tree["month_epoch"] = {"node": Node("month_epoch", parent=tree["month"]["node"])}
        tree["season_epoch"] = {"node": Node("season_epoch", parent=tree["season"]["node"])}

        return tree


    def to_dict(self):
        d = {}
        for field, dtype in self.fields.items():
            v = getattr(self, field)
            if v is not None:
                d[field] = dtype(v)
        return d


    def string_parts(self, month_and_day=True, specify_ad=False, abbreviate=False):
        parts = pd.Series()
        if self.fuzzy:
            parts["fuzzy"] = "c."
        if month_and_day:
            if self.day is not None:
                parts["day"] = str(int(self.day))
            if self.month_epoch is not None:
                parts["month_epoch"] = self.month_epoch.capitalize()   
            if self.month is not None:
                parts["month"] = self.month.capitalize()
                if abbreviate:
                    parts["month"] = parts["month"][:3]
        if self.year_epoch is not None:
            parts["year_epoch"] = self.year_epoch.capitalize()
        if self.year is not None:
            parts["year"] = str(abs(self.numerical_year))
            if self.era == "BC":
                parts["year"] = parts["year"] + " BC"
            elif specify_ad:
                parts["year"] = "AD " + parts["year"] 
        return parts.to_dict()
    

    def string(self, **string_part_kwargs):
        parts = self.string_parts(**string_part_kwargs)
        return " ".join(list(parts.values()))
    

    def __repr__(self):
        
        lines = []
        for tree_key in ["fuzzy", "year"]:
            for pre, fill, node in RenderTree(self.tree[tree_key]["node"]):
                value = self.tree[node.name].get("value")
                if isinstance(value, list):
                    value = "/".join(value)
                if value is not None:
                    if node.depth > 0:
                        pre = "    " * (node.depth - 1) + "└── "
                    else:            
                        pre = ""
                    lines.append(f"{pre}{node.name}: {value}")
        return "\n".join(lines)


                


class Place:
    """
    A country is something that might have a flag
    """

    def __init__(self, d):

        self.data = copy.deepcopy(d)


    def flag(self):
        if self.country in flags.loc[:, "name"].values:
            return flags.set_index("name").loc[self.country, "emoji"]
        return ""

                    
    def __getattr__(self, attr):

        if attr in self.data:
            return self.data[attr]
        else:
            raise KeyError(f"No attribute '{attr}'.")

    def string(self):       
        if self.data is not None:
            return ", ".join([s for s in self.data.values()])
        return ""

    def __repr__(self):
        return f"Place({self.data})"

class Spacetime:

    def __init__(self, time: Time = None, place: Place = None):

        self.time = time
        self.place = place

    def __repr__(self):

        return f"Spacetime(time={self.time.to_dict()}, place={self.place.data})"

    
    def string(self, key="time", kwargs={"abbreviate": True}, html=None, html_kwargs={}):

        if key not in ["time", "place"]:
            raise ValueError()
        
        s = f"{getattr(self, key).string(**kwargs)}"
        
        if html in ["time", "place"]:
            html_attr = getattr(self, html)
            if html_attr is not None:
                s = f'<span title="{html_attr.string(**html_kwargs)}">{s}</span>'
        
        return s
                    
    def __getattr__(self, attr):

        if attr in self.data:
            return self.data[attr]
        else:
            raise KeyError(f"No attribute '{attr}'.")


class TimeRange:

    def __init__(self, 
                 start: Time, 
                 end: Time):
        
        self.start = start 
        self.end = end
