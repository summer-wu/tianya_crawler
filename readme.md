# 天涯爬虫
+ 原因：天涯的导航并不完整，我想弄清天涯到底有多少个版块。
+ 方法：先获取顶层板块，然后找到相关板块。这样就可以找到所有版块了。
+ 获取的信息：主帖数、回帖数、开版时间、本版介绍、bbsGlobal

# 具体过程
+ 先手动创建tianya_blocks.json，它是导航中列出的板块，直接从html中获取
+ 在爬取的过程更新tianya_blocks.json和data.json
+ data.json只有一层，保存详细信息。tianya_blocks.json有两层，只保存链接