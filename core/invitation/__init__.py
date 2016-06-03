# -*- coding: utf-8 -*-
import uuid
import random, string

phone_hash_words = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']


def generate_from_phone(ll):
    ll = int(ll)
    # set = []
    # for i in range(48, 57+1, 1):
    #     set.append(chr(i))
    # for i in range(65, 90+1, 1):
    #     set.append(chr(i))

    num = ll % 10000000000
    binary = bin(num)
    str_bin = str(binary)[2:]

    str_bin = '{:0>40s}'.format(str_bin)
    # if len(str_bin) < 40:
    #     temp_str = ''
    #
    #     for i in range(0, 40-len(str_bin), 1):
    #         temp_str += '0'
    #
    #     str_bin = temp_str+str_bin

    code = ''
    for i in range(0, 40, 5):
         index = int(str_bin[i:i+5], 2)
         # code += set[index]
         code += phone_hash_words[index]
    return code


def generate_from_execution(execution):
    gen_uuid = str(uuid.uuid4())
    tmp_str = gen_uuid[:4]  # uuid 前4位

    tmp_str += string.ascii_lowercase[execution.id % len(string.ascii_lowercase)] # 根据id获取2位
    tmp_str += string.digits[execution.id % len(string.digits)]

    tmp_str += random.choice(execution.phone)

    tmp_list = [_ for _ in tmp_str]
    random.shuffle(tmp_list)

    return ''.join(tmp_list)