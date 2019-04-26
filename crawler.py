import os, sys
import json
import urllib.request
from http.client import HTTPResponse
from html.parser import HTMLParser
from html.entities import name2codepoint
import traceback
import logging
logging.root.setLevel(logging.CRITICAL)

c_filename_data = "data.json"  # 记录单独板块
c_filename_blocks = "tianya_blocks.json"  # 记录所有的板块，包括子级别


class TYHTMLParser(HTMLParser):
  """它会记住主贴数、回帖数、板块描述、开板时间、相关板块"""

  def __init__(self):
    super().__init__()
    self.countSubject = None
    self.countReplies = None
    self.startAt = None
    self.desc = None
    self.bbsGlobal = None

    self.attrs = None  # 当前tag的attrs
    self.nextIsStartAt = False  # 标记下一个Data是开版时间
    self.nextIsDesc = False
    self.xiangguanBlocks = []  # 相关板块

    self.xiangguanStart = False
    self.openingTagCount = 0  # 记录有多少打开的tag

  def handle_starttag(self, tag, attrs):

    logging.debug("Start tag:"+ tag)
    self.attrs = dict(attrs)
    if 'id' in self.attrs and self.attrs['id'] == 'main_xiangguan':
      self.xiangguanStart = True

    if self.xiangguanStart:  # 仅在相关板块div中才记录openingTagCount
      self.openingTagCount += 1
      if tag == 'a':
        href = self.attrs['href']
        href_abs = 'http://bbs.tianya.cn' + href
        self.xiangguanBlocks.append(href_abs)

    for attr in attrs:
      logging.debug("     attr:"+ str(attr))

  def handle_endtag(self, tag):
    self.attrs = None
    logging.debug("End tag  :"+ tag)

    if self.xiangguanStart:
      self.openingTagCount -= 1
      logging.debug("openingTagCount=", self.openingTagCount)
      if self.openingTagCount == 0:
        self.xiangguanStart = False

  def handle_data(self, data):
    logging.debug("Data     :"+ data)

    if self.nextIsStartAt:
      self.startAt = data
      self.nextIsStartAt = False
      return

    if self.nextIsDesc:
      self.desc = data
      self.nextIsDesc = False
      return

    if "主帖数：" in data:
      self.countSubject = self.attrs['title']
    elif '回帖数：' in data:
      self.countReplies = self.attrs['title']
    elif '开版时间：' == data:
      self.nextIsStartAt = True
    elif '本版介绍：' == data:
      self.nextIsDesc = True
    elif 'bbsGlobal' in data:
      left = data.index('{')
      right = data.index('}')
      bbsGlobal = data[left:right+1]
      bbsGlobal = bbsGlobal.replace("\t",'"')
      bbsGlobal = bbsGlobal.replace(" :",'":')
      self.bbsGlobal = json.loads(bbsGlobal)
      print("bbsGlobal:",bbsGlobal)
    else:
      self.nextIsStartAt = False
      self.nextIsDesc = False

  def handle_comment(self, data):
    logging.debug("Comment  :"+ data)

  def handle_entityref(self, name):
    c = chr(name2codepoint[name])
    logging.debug("Named ent:"+ c)

  def handle_charref(self, name):
    if name.startswith('x'):
      c = chr(int(name[1:], 16))
    else:
      c = chr(int(name))
      logging.debug("Num ent  :"+ c)

  def handle_decl(self, data):
    logging.debug("Decl     :"+ data)


class TianYa:
  def __init__(self):
    pass

  def saveTo_tianya_blocks(self, block, upperBlock=None):
    """block是板块网址，upperBlock上级板块网址。最多只有两级"""
    if not os.path.exists(c_filename_blocks):
      with open(c_filename_blocks, "w") as f:
        json.dump({"": ""}, f)

    with open(c_filename_blocks, "r") as f:
      d = json.load(f)
    if upperBlock is None:
      d[block] = {}
    else:
      d[upperBlock][block] = None

    with open(c_filename_blocks, "w") as f:
      json.dump(d, f, indent=4)

  def getBlocks(self)->dict:
    """读取json"""
    with open(c_filename_blocks, "r") as f:
      d = json.load(f)
      return d

  def fetchInfoOfBlock(self, block, isSubBlock):
    """获取版块信息，获取后更新两个json文件"""
    logging.critical("will fetch "+ block)
    if self.isBlockAlreadyFetched(block):
      logging.critical(("已经获取过了 "+ block))
      return
    try:
      response: HTTPResponse = urllib.request.urlopen(block)
    except:
      print(f"fetchInfoOfBlock {block} 出错")
      traceback.print_exc()
      return
    htmlstr = response.read().decode()
    parser = TYHTMLParser()
    parser.feed(htmlstr)

    self.saveDataWithBlock(block,parser.countSubject,parser.countReplies,
                           parser.startAt,parser.desc,parser.bbsGlobal)

    #仅顶层版块处理
    if not isSubBlock:
      for subBlock in parser.xiangguanBlocks:
        self.saveTo_tianya_blocks(subBlock,upperBlock=block)

  def start(self):
    for block,subBlockDict in self.getBlocks().items():
      self.fetchInfoOfBlock(block, isSubBlock=False)
      if len(subBlockDict)>0:
        for block,_ in subBlockDict.items():
          self.fetchInfoOfBlock(block, isSubBlock=True)

  def getInfoFromHTMLStr(self, htmlstr):
    parser = TYHTMLParser()
    parser.feed(htmlstr)
    print(vars(parser))

  def saveDataWithBlock(self,block,countSubject,countReplies,startAt,desc,bbsGlobal):
    """将获取到的数据保存到json中。block、对应主帖数、回帖数、开版时间、本版介绍"""
    if os.path.exists(c_filename_data):
      with open(c_filename_data,'r') as f:
        d = json.load(f)
    else:
      d = {}

    item = dict(countSubject=countSubject,countReplies=countReplies,
                startAt=startAt,desc=desc,bbsGlobal=bbsGlobal)
    d[block] = item

    with open(c_filename_data,'w') as f:
      json.dump(d,f,indent=4,ensure_ascii=False)

  def isBlockAlreadyFetched(self,block):
    """看看block是否已经获取过了"""
    if os.path.exists(c_filename_data):
      with open(c_filename_data,'r') as f:
        d = json.load(f)
        return block in d
    return False


if __name__ == '__main__':
  t = TianYa()
  t.start()
