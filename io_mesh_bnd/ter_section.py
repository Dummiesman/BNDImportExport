# ##### BEGIN LICENSE BLOCK #####
#
# This program is licensed under Creative Commons BY-NC-SA:
# https://creativecommons.org/licenses/by-nc-sa/3.0/
#
# Created by Dummiesman, 2016-2020
#
# ##### END LICENSE BLOCK #####

class TerSection:
    def __init__(self, bounds_min, bounds_max, edges, polygon):
        self.edges = edges
        self.bounds = (bounds_min, bounds_max)
        self.polygon = polygon
        self.group = []
        
