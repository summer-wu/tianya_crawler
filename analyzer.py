"""读取data.json，生成csv格式，放到表格里进行分析"""

import os, sys
import json

c_filename_data = "data.json"

class Analyzer:
  def __init__(self):
    pass

  def getData(self):
    with open(c_filename_data) as f:
      d = json.load(f)
      return d

  def printCount(self):
    d = self.getData()
    for block,item in d.items():
      name = item['bbsGlobal']['itemName']
      countSubject = item['countSubject']
      itemType = item['bbsGlobal']['itemType']
      itemCategory = item['bbsGlobal']['itemCategory']
      line = f"{name},{countSubject},{itemType},{itemCategory}"
      print(line)


if __name__ == '__main__':
  a = Analyzer()
  a.printCount()
