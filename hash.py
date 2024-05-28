import math

def hash_list(num):
    numbers = list(range(0, 10))
    letters = ['A', 'B', 'C', 'D', 'E', 'F']
    num_element = numbers + letters
    max_amount = max(int(math.log2(num) / 4) + 1, 3)
    ans_list = list()
    def update_hash(middle_hash):
        if len(middle_hash) == max_amount:
            ans_list.append(middle_hash)
        else:
            for numeral in num_element:
                if len(ans_list) == num:
                    return
                update_hash(middle_hash + str(numeral))
    update_hash("")
    return ans_list

