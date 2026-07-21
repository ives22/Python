"""
# 变量定义练习
st1 = "正是奋斗的年纪"
in1 = 30
fl1 = 29.8
print(st1)
print(in1)
print(fl1)

# 获取数据类型
print(st1, type(st1), in1, type(in1), fl1, type(fl1))

# 类型转换
st2 = "222"
in2 = 302
fl2 = 3.14
print(int(st2), type(int(st2)))      # str   -> int
print(float(st2), type(float(st2)))  # str   -> float
print(str(in2), type(str(in2)))      # int   -> str
print(float(in2), type(float(in2)))  # int   -> float
print(str(fl2), type(str(fl2)))      # float -> str
print(int(fl2), type(int(fl2)))      # float -> int


# # 字符串格式化+input练习
# date = input("请输入今天的日期: ")
# weather = input("请输入今天的天气: ")
# temperature = input("请输入今天的温度: ")
# # 格式化方式1
# str2 = f"今天是：{date}，天气：{weather}, 温度：{temperature}°C "
# # 格式化方法2
# str3 = "今天是: %s，天气：%s，温度：%.2f°C" %(date, weather, float(temperature))
# print(str2)
# print(str3)



# while 循环

i = 1
while i <= 100:
    print(i)
    i+=1


i = 1
while i <= 9:
    j = 1
    while j <= i:
        print(f"{j} * {i} = {j*i}\t", end="")
        j+=1
    i+=1
    print()


# for 循环
st1 = "itheima is a brand of itcast"
count = 0
for i in st1:
    if i == "a":
        count += 1
print(f"{st1}共有{count}个a")


# range语法1 range(num)
for x in range(10):
    print(x)

for x in range(5,10):
    # 从5开始，到10结束，不包含10本身
    print(x)

for x in range(5,10,2):
    # 从5开始，到10结束，数字之间的间隔是2
    print(x)



str1 = "itheima"
str2 = "itcast"
str3 = "python"

count = 0
for i in str1:
    count += 1
print(f"字符串{str1}的长度是: {count}")

count = 0
for i in str2:
    count += 1
print(f"字符串{str2}的长度是: {count}")

count = 0
for i in str3:
    count += 1
print(f"字符串{str3}的长度是: {count}")


def my_len(data):
    count = 0
    for i in data:
        count += 1
    print(f"字符串{data}的长度是：{count}")

my_len(str1)
my_len(str2)
my_len(str3)

"""


# ========================== 函数的定义

# 定一个一个函数，输出相关信息
def say_hi():
    print("Hi, I am ")


say_hi()


# 带参数的函数
def add(x, y):
    result = x + y
    print(f"{x} + {y} = {result}")


add(1, 2)


# 函数的返回值
def add_v1(x, y):
    result = x + y
    return result


r = add_v1(1, 2)
print(r)


# 函数参数的默认值,
def func_01(x, y=2):
    print("x: %d, y: %d" % (x, y))


func_01(1)  # 如果y值没有传值则使用默认值
func_01(2, 3)  # 如果y值传值则替换默认值

# ========================== 列表
# 列表的定义
l1 = [1, 2, 3]
l2 = list()
l3 = [1, "s1", 3.14]  # 列表中可以存放任意数据类型
l4 = ["s1", 123, 3.23, [1, 2, 3]]
print(f"l1: {l1}, type(l1): {type(l1)}")
print(f"l2: {l2}, type(l2): {type(l2)}")
print(f"l3: {l3}, type(l3): {type(l3)}")
print(f"l4: {l4}, type(l4): {type(l4)}")

# 列表的取值
print(l1[0])
print(l1[1])
print(l1[2])
# print(l1[3])  # 索引越界会报错：IndexError: list index out of range
print(l1[-1])

# 列表的方法
print(l1.index(2))  # index：查找元素在列表中的索引位置
print(l1.count(2))  # count: 统计元素在列表中出现的次数
l1.insert(1, 10)  # insert： 向指定索引位置插入数据
print(l1)
l1.append(1010)  # append：在列表的最后追加元素
print(l1)
l2 = [222, 333, 444]
l1.extend(l2)  # extend：将一个列表添加到列表中
print(l1)



from urllib.parse import quote

base_url = "https://gitlab.fluence.com"

branch = "5500"

a = quote("test/opc", safe='')
print(a)





""" 
验证partition方法
"""
client_data = {
    "username": "admin",
    "c_name": "admin@12312312"
}

u_name = client_data['username'].partition('@')[0].lower()
c_name = client_data['c_name'].partition('@')[0].lower()
print(u_name)
print(c_name)



import re
test_key = {"client1": "123456,2323"}
st1 = "123456,2343"
allowed_mac_set = {m.strip().lower() for m in re.split(r'[;,]', st1) if m.strip()}
print(allowed_mac_set)




import os
def load_hwaddr_whitelist(file_path: str, separators: list) -> set:
    """
    加载硬件地址白名单

    文件格式：一行一个硬件地址
    支持格式：
    - MAC 地址：00:11:22:33:44:55
    - UUID/Machine ID: 550e8400-e29b-41d4-a716-446655440000

    separators: 支持的分隔符列表，如：[':', '=', '|']
    返回：硬件地址集合（小写）
    """
    hwaddr_set = set()

    if not os.path.exists(file_path):
        return hwaddr_set

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                content = line.strip()
                # 跳过空行和注释
                if not content or content.startswith('#'):
                    continue

                for s in separators:
                    content = content.replace(s, '|')

                parts = content.split('|')
                if len(parts) >= 2:
                    hwaddr_set.add(parts[1].strip().lower())

    except Exception as e:
        print(f"Error: {e}")

    return hwaddr_set


result = load_hwaddr_whitelist("/Users/liyj/Documents/Code/Github/Python/practise/macaddr", ["="])
print(result)