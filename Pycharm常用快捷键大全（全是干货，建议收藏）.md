  

我们写代码的时候回发现有很多黄色的波浪号，类似下图中的  
这个时候可以点击任意黄色波浪号的代码，然后按下【Ctrl + Alt + L】进行代码格式化  
![](https://i-blog.csdnimg.cn/img_convert/61fe8360143a3d614c2d4c7d7a9d9723.png)

格式化效果

```cobol
 def x():    a = 1    b = [1, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 123, 12, 31, 231, 23, 123, 1, 231, 23, 123, 1, 43, 53, 643, 53, 4, 24, 12, 31,         231, 23, 123, 24, 53, 4534, 2, 1231, 23, 1]    print(a)  x()
```

**2\. 多行代码合并为一行【Crtl+Shift+J】**
-------------------------------

如果想将下图的代码合并为一行，可以全选它们，然后按【Crtl+Shift+J】即可合并代码为一行，还会自动补充代码

```cobol
x=1y=1z=1
```

合并后的效果

```cobol
x=1; y=1; z=1
```

\===

**3\. 修正报警告的代码【Ctrl + Enter】**
------------------------------

当出现黄色波浪号时，可以在对应代码出按下【Ctrl + Enter】进行修正代码的操作  
![](https://i-blog.csdnimg.cn/img_convert/3249401db32626c60ca9105a5f717d84.png)

按下后，会有多种选择供你修正，包括:格式化代码，忽略该警告，自动修改代码等

![](https://i-blog.csdnimg.cn/img_convert/974481cd3ec1632d6a0ce1335fb8f2ea.png)

例如选择:【invert ‘if’ condition】会自动改成下面的代码：

```cobol
def test(x):    if 1 != 1:        return    pass
```

\===

**4 .包装代码【Crtl+Alt+T】**
-----------------------

我们可以快速的为输入的代码添加if、while、捕获异常等条件  
例如有如下代码

```cobol
x=1
```

我们选中该代码后按下【Crtl+Alt+T】会弹窗让我们选择要包装的条件，现在我们选择【try/except】

![](https://i-blog.csdnimg.cn/direct/55a48a3080a843969d9e42139e583b13.png)

包装效果

```python
try:    x=1except:    pass
```

**5\. 快速注释/取消注释【Crtl+/】**
-------------------------

如果我们想注释一部分代码可以选中对应的代码，并按下【Crtl+/】

```scss
 def show_text(text,a):    a+=1    print(text,a)
```

注释结果

```csharp
# def show_text(text,a):#     a+=1#     print(text,a)
```

再次按下【Crtl+/】则会取消注释

**6\. 向右缩进一个制表位【Tab】**
----------------------

python 对代码的缩进要求很严格，下面的代码运行是会报错的！

```cobol
 def test():y = 1y += 1print(y)
```

但一行一行的去调整缩进非常难受，效率很低！这时候可以选中需要缩进的代码，按下【Tab】即可

效果

```cobol
 def test():    y = 1    y += 1    print(y)
```

**7\. 向左缩进一个制表位【Shift + Tab】**
------------------------------

同上

**8\. 在上方插入新行【Ctrl + Alt + Enter】**
-----------------------------------

如果想在下面代码`a+=1`的上方插入空行的话，可以点击到`a+=1`这行，然后按下【Ctrl + Alt + Enter】，则会在其上方新插入一行

```scss
 def show_text(text,a):    a+=1    print(text,a)
```

效果

```scss
 def show_text(text,a):        a+=1    print(text,a)
```

\===

**9\. 在下方插入新行【Shift + Enter】**
------------------------------

同上

**10\. 上下移动选中代码【Alt + Shift + 上、下键】**
-------------------------------------

如果我们想将下面代码的`a=1`移动到`print('click')`上方，可以在`a=1`的所在行按下【Alt + Shift + 上】将其移动

```scss
   def click(path):    print('click')    a = 1
```

效果

```scss
 def click(path):    a = 1    print('click')
```

向下移动则按【Alt + Shift + 下】即可！

**11\. 上下移动选中方法体【Ctrl + Shift + 上、下键】**
---------------------------------------

如果我们想将下面的`send`方法移动到`click`方法的上方，可以在`send`方法名这行(def 所在行)按下【Ctrl + Shift + 上】即可

```python
 def click(path):    print('click') def send(path):    print('send')
```

效果

```python
 def send(path):    print('send') def click(path):    print('click')
```

向下移动则按【Ctrl + Shift + 下】即可！

**12\. 复制代码【Ctrl + D】**
-----------------------

如果我们想复制一行代码，可以在相应代码行按下【Ctrl + D】

```cobol
x=y=z=1
```

效果

```cobol
 x=y=z=1x=y=z=1
```

也可以选中多行代码进行复制

```scss
 def show_text(text,a):    a+=1    print(text,a)
```

效果

但需要自己换行

```python
 def show_text(text,a):    a+=1    print(text,a)def show_text(text,a):    a+=1    print(text,a)
```

**13\. 折叠代码【Ctrl + -】**
-----------------------

想折叠下面的代码的话，可以选中代码再按下【Ctrl + -】

```scss
 def show_text(text,a):    a+=1    print(text,a)
```

效果

```scss
def show_text(text,a):...
```

**14\. 展开代码【Ctrl + +】**
-----------------------

同上

**15\. 将代码抽取为一个方法【Ctrl + Shift+M】**
-----------------------------------

如果想将如下的代码，写到一个方法中的话，可以选中代码并按下【Ctrl + Shift+M】

```cobol
 y=1y+=1print(y)
```

然后重命名方法，再点击【ok】

![](https://i-blog.csdnimg.cn/direct/501ed0145d0d4002988bd36fb40f8497.png)

效果

```cobol
 def test():    global y    y = 1    y += 1    print(y)  test()
```

**16\. 重命名文件【Shift+F6】**
------------------------

需要重命名文件名时，可以选择对应文件按下【Shift+F6】，再输入框输入新的文件名再点击【Refactor】即可​​​​​​​![](https://i-blog.csdnimg.cn/direct/c79c1272b71848eca9ce268419abe9aa.png)

效果  
![](https://i-blog.csdnimg.cn/img_convert/ee1932639553af439358df1bc6fc1738.png)

**17\. 查找类被引用的地方【Ctrl+N】**
--------------------------

按下【Ctrl+N】输入类的关键字，就可以看到被引用的类，点击对应的条目可跳转到对应文件​​​​​​​![](https://i-blog.csdnimg.cn/direct/cd5749b4bfe24f4d8df3db63ca5ec409.png)

**18\. 查找/全局查找【Ctrl+F / Ctrl + Shift+F】**
-----------------------------------------

当前文件的查找可以按下【Ctrl+F 】并输入要查找的关键字就会高亮包含关键字的代码

![](https://i-blog.csdnimg.cn/direct/d72ad85898db4169b7dc0c6a0d70fb82.png)

点击图中红款的箭头，可以逐行查看包含关键字的代码；另外，按下【Shift + F3】或【F3】也可以实现！

![](https://i-blog.csdnimg.cn/img_convert/e6f52f67847ed2def5499575e3141d41.png)

点击红框中的窗口图标，可以打开TOOL窗口进行多窗口查询​​​​​​​![](https://i-blog.csdnimg.cn/direct/400250b313d24fe8988a01147fa5e201.png)

效果​​​​​​​![](https://i-blog.csdnimg.cn/direct/62e822144885431ba67bf0a0aa45fdf8.png)

全局查询的话按下【Ctrl + Shift+F】即可！

**19\. 替换/全局替换【Ctrl+R / Ctrl + Shift+R】**
-----------------------------------------

当前文件的替换可以按下【Ctrl+R 】并在第一栏输入要替换的关键字就会高亮包含关键字的代码，第二栏输入要替换为的关键字，在按下【replace】或【replace All】(替换全部)​​​​​​​![](https://i-blog.csdnimg.cn/direct/0aec6bcf23494488a25c0c3a3b50e746.png)

效果  
![](https://i-blog.csdnimg.cn/direct/eb258284bbb347c4ac17c4f7c08d417d.png)下图红框中的【exclude】点击的话，会排除选中的该代码，只替换其他代码​​​​​​​![](https://i-blog.csdnimg.cn/direct/851f802956254891b9902756af0c66f6.png)

效果

![](https://i-blog.csdnimg.cn/direct/846902e9d0704425ba08452afe34858f.png)

全局替换的话按下【Ctrl + Shift+R】即可！

**20\. 快速跳转报错的代码【F2】**
----------------------

当出现代码报错的时候，可以按下F2快速跳转到报错的代码处  
![](https://i-blog.csdnimg.cn/img_convert/ab22c446de589e8530dd336b70709447.png)

效果  
![](https://i-blog.csdnimg.cn/img_convert/8bf56bda39a4c918cb0df84d1b87653a.png)

**21\. 定义一个书签【F11】**
--------------------

在相应代码处按下【F11】可以将其定义为一个书签  
![](https://i-blog.csdnimg.cn/img_convert/a211d9d3d72822c1c5baf287a6aa67d1.png)

再按下【Shift+F11】，可以查看书签对应的代码  
![](https://i-blog.csdnimg.cn/img_convert/541357c4b95f9673f5a8e403064f1428.png)

**22\. 代码小写转大写【Ctrl + Shift+U】**
--------------------------------

如果想将下面的代码转为大写，可选中代码后按下【Ctrl + Shift+U】

```cobol
product_nama_dict={}
```

效果
--

```cobol
PRODUCT_NAMA_DICT={}
```

**23\. 进入一个方法【Ctrl + B / Ctrl +鼠标左键】**
--------------------------------------

如果想进入time模块的方法中去，可以选中【time】再按下【Ctrl + B 】，或者按下【ctrl+鼠标左键】

效果  
![](https://i-blog.csdnimg.cn/img_convert/7014d2b6e4de3cc5f2030e32f3d4d6d9.png)

**24\. 快捷查看方法的实现(源码)【Ctrl + Shift + I】**
----------------------------------------

如果我们想看【time】是如何实现的，可以选中并按下【Ctrl + Shift + I】

```less
 import timetime.sleep()
```

效果  
![](https://i-blog.csdnimg.cn/img_convert/69c75aebcb0c42cb030ac5b7bc265d0a.png)

**25\. 查看文档描述【Ctrl + Q】**
-------------------------

如果我们想看【time】的文档，可以选中并按下【Ctrl + Q】

```less
 import timetime.sleep()
```

效果  
![](https://i-blog.csdnimg.cn/img_convert/abf1985f3ee382ea961c5256d64463b4.png)

**26\. 查看文件中的方法【Ctrl + F12】**
-----------------------------

按下【Ctrl + F12】可以看该文件中有哪些方法、类

**27\. 最近编辑的文件列表【Ctrl + E】**
----------------------------

![](https://i-blog.csdnimg.cn/img_convert/ce183775850657d93633dca6def2612c.png)

**28\. 快捷运行代码【Shift + F10】**
----------------------------

快捷运行当前文件代码

**29\. 快捷调试代码【Shift + F9】**
---------------------------

快捷调试当前文件代码

**30\. 快捷切换视图/目录【Ctrl + Tab】**
------------------------------

![](https://i-blog.csdnimg.cn/img_convert/f414a5369409158e8441bbd56f272769.png)

![](https://i-blog.csdnimg.cn/img_convert/9a5da8fef3dcad1099448b45eb765175.png)

**31\. 查看最近更改【Alt + Shift + C】**
--------------------------------

![](https://i-blog.csdnimg.cn/img_convert/fcdaa3bb52b096216e91c0df6d9a7eb4.png)

**32\. 将光标移动到代码行尾【End】**
------------------------

当你的代码很长的时候，已经超过屏幕显示范围了！  
可以按下【End】(笔记本一般为【Fn+End】)可以跳转到行尾

![](https://i-blog.csdnimg.cn/img_convert/b7f9a148396c31ad5fcf576e65f8ada6.png)

效果  
![](https://i-blog.csdnimg.cn/img_convert/2c15d7508d8893e1c3148293a671575b.png)

按下【Home】(笔记本一般为【Fn+Home】)可回到行首！

**33\. 全选一行并移至行尾【Shift + End】**
-------------------------------

**效果**  
![](https://i-blog.csdnimg.cn/img_convert/935392b9443f97fa40ee69f505d71dd7.png)

**34\. 查看历史粘贴复制记录【Ctrl + Shift+ V】**
------------------------------------

按下【Ctrl + Shift+ V】可以查看历史的复制粘贴记录  
![](https://i-blog.csdnimg.cn/img_convert/a5b1825689ae9dfcd46d285df04c3617.png)

选择任意一行可以将它恢复回来

```less
 @api_view(['PATCH'])@permission_classes((IsAuthenticated,))def set_client_debug(request):    Client.objects.filter(user_id=request.user.id).update(debug=request.data['debug'])    return Response(data={'code': 0})
```

**35\. 将光标移动到方法体或循环的开始【Ctrl + {】**
----------------------------------

当你的方法或循环体很长的时候，可以按下【Ctrl + {】回到函数或循环头

**36\. 将光标移动到方法体或循环的结束【Ctrl + ｝】**
----------------------------------

当你的方法或循环体很长的时候，可以按下【Ctrl + }】回到函数尾或循环尾

**37\. 最大化编辑代码窗口【Ctrl + Shift + F12】**
--------------------------------------

当我们打开了多窗口的时候，影响了代码编辑体验的时候，如下图所示，可以按下【Ctrl + Shift + F12】隐藏其他窗口  
![](https://i-blog.csdnimg.cn/img_convert/7bf8cbb59a645c87db93fc2acf19ad59.png)

**效果**  
![](https://i-blog.csdnimg.cn/img_convert/002fa12f30a1e1af56ce8b1fc7090ef6.png)

**38\. 快捷添加代码【Ctrl + J】**
-------------------------

按下【Ctrl + J】可以快速 添加代码  
![](https://i-blog.csdnimg.cn/img_convert/007eda6b06d71857786e9fafa878cbbd.png)

例如添加`if __name__ == __main__`，点击上图的【main】即可:

```cobol
 if __name__ == '__main__':
```

* * *

 希望这篇文章对正在学习编程的你有所帮助，如果你想学习编程，那给大家分享一份Python学习资料，里面的内容都是适合零基础小白的笔记和资料，不懂编程也能听懂、看懂。如果需要的话直接划到文末免费获得，让我们一起学习！

![在这里插入图片描述](https://i-blog.csdnimg.cn/blog_migrate/7aa3ec1b3da583abcd8490cd15cddef7.png)

![](https://i-blog.csdnimg.cn/direct/1420cbbf5c194c94af7394c423519efb.jpeg)

本文转自 <https://blog.csdn.net/2301_78095812/article/details/145300604>，如有侵权，请联系删除。