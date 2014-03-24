#!/usr/bin/python
#! --encoding:utf-8--

def make_tree(dic):
    '''
    根据Nagios中保存的每个节点的父节点
    前序遍历树并生成各个子树中节点的有序列表
    '''
    def find_roots(key, l):
        v = dic.get(key)
        if v != None:
            find_roots(v, l)
        l.append(v)
    
    roots = []
    for k, v in dic.items():
        l = []
        find_roots(k, l)
        if len(l) == 2:
            roots.append(l[1])
        if len(l) == 1:
            roots.append(k)
    
    real_roots = list(set(roots))
    
    def find_child(root, l):
        for k, v in dic.items():
            if v == root:
                l.append(k)
                find_child(k, l)
    
    final_data = []
    
    for root in real_roots:
        temp = {}
        l = []
        find_child(root, l)
        temp['root'] = root
        temp['child'] = l
        final_data.append(temp)
    
    return final_data


if __name__ == '__main__':
    
    # make simple test

    dic = {
        "N1": "M1",
        "M1": "A1",
        "Z1": "A1",
        "A1": "B1",
        "B1": "C1",
        "D1": "C1",
        "E1": "C1",
        "C1": None,
        "X1": None,
        "Y1": "X1",
        "G1": None,
        "K1": "Y1",
    }
    
    tree = make_tree(dic)
    print tree


