"""
@Description:
@FilePath:
"""


# 位置参数
def login(username, password):
    if username == "admin" and password == "123":
        print("登录成功")
    else:
        print("登录失败")


login("admin", "123")
login("admin", "1232")


# 默认值参数
def get_book(book, number=1, school="北京大学"):
    print("欢迎来到{}借书系统...".format(school))
    print("借了图书《{}》，共计{}本".format(book, number))


get_book("西游记")
get_book("红楼梦", 2)
get_book("三国演义", school="清华大学")


# 可变参数 *args
def my_sum(a, b):
    print(a + b)


my_sum(1, 2)


# 如果此时要计算 1+2+3+4+5+6+7+8+9，不可能就修改求和函数的参数
def my_sum_v1(*args):  # * 会进行装包，将传入的多个参数放在一个元组里面
    print(args, type(args))
    s = 0
    for i in args:
        s += i
    print(s)


my_sum_v1(1, 2)

# 底层逻辑分析
a, b, c = 1, 2, 3
print(a)  # 1
print(b)  # 2
print(c)  # 3

a, b, *c = 1, 2, 3, 4, 5, 6, 7
print(a)  # 1
print(b)  # 2
print(c)  # [3, 4, 5, 6, 7]

a, *b, c = 1, 2, 3, 4, 5, 6, 7
print(a)  # 1
print(b)  # [2, 3, 4, 5, 6]
print(c)  # 7

l = [1, 2, 3, 4, 5, 6, 7]
# 现在想要把这个列表 l 传递给 my_sum_v1 进行求和
# 可以通过 * 对l进行拆包，然后传递
my_sum_v1(*l)


# **kwargs
def get_books(**kwargs):
    print(kwargs, type(kwargs))


get_books()

get_books(a=3, b=2)
d = {"name": "张三", "hobby": "唱歌"}
get_books(**d)


# 参数混合使用示例
def f_args(name, *args, **kwargs):
    print("name: {}".format(name))
    for arg in args:
        print("args->{}".format(arg))
    for k, v in kwargs.items():
        print("{}->{}".format(k, v))


f_args("张三", "唱歌", "跳舞", sex="男", age=18)



# 闭包
"""
1、一个函数引用外部变量；
2、
"""

def inner(n):
    def outer():
        # print("x", x)
        return n + 1
    return outer
r = inner(2)
print(r())



"""
装饰器 ==================================
"""

def fun1(a):
    print(a)

def fun2(a):
    print(a)

def fun3(a):
    print(a)


def check_login():
    print("校验登录")

fun1(1)
fun2(2)
fun3(3)


def fun1_1(a):
    check_login()
    print(a)
def fun2_1(a):
    check_login()
    print(a)
def fun3_1(a):
    check_login()
    print(a)

fun1_1(1)
fun2_1(2)
fun3_1(3)


def check_login(func):
    def wrapper():
        print("校验登录")
        func()
    return wrapper

@check_login
def fun1_2():
    print("fun1_2")
def fun2_2():
    print("fun2_2")
def fun3_2():
    print("fun3_2")


fun1_2()
# fun2_2(2)
# fun3_2(3)

'''
带参数的装饰器
'''

def decorater(func):

    def wrapper(address):
        func(address)
        print('刷漆')
        print('买家具')
    return wrapper

@decorater
def house(address):
    print('房子的地址是:{}'.format(address))


house("北京四合院")
