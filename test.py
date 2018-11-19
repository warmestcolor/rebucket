import json
import rebucket
from rebucket import Stack
from rebucket import Frame

def read_dataset(json_path):
    with open(json_path) as json_file:
        dataset_dict = json.load(json_file)
    all_stacks = []
    for stack_dict in dataset_dict:
        stack_id = stack_dict['stack_id']
        duplicated_stack = stack_dict['duplicated_stack']
        frame_arr = []
        for fram_dict in stack_dict['stack_arr']:
            frame = Frame(fram_dict)
            frame_arr.append(frame)
        all_stacks.append(Stack(stack_id, frame_arr, duplicated_stack))
    return all_stacks


def generate_realbuckets(stacks):
    real_buckets = []
    
    for stack in stacks:
        if len(stack.duplicated_stack) is not 0:
            in_bucket = False
            for bucket in real_buckets: 
                if stack.duplicated_stack in bucket:
                    bucket.append(stack.id)
                    in_bucket = True
                    break
            if not in_bucket:
                for d_stack in stacks:
                    if d_stack.id == stack.duplicated_stack:
                        real_buckets.append([d_stack.id, stack.id])
        else:
            already_have = False
            for bucket in real_buckets:
                if stack.id in bucket:
                    already_have = True
            if not already_have:
                real_buckets.append([stack.id])  
    #     if len(stack.duplicated_stack) is not 0:
    #         found = False
    #         for bucket in real_buckets: 
    #             if stack.duplicated_stack in bucket:
    #                 bucket.append(stack.duplicated_stack)
    #                 found = True
    #             else:
    #                 for tmp_stack in stacks:
    #                     if tmp_stack.id == stack.duplicated_stack:
    #                         bucket.append(stack.duplicated_stack)
    #                         found = True
    #         if found:
    #             continue
    #     real_buckets.append([stack.id])
    return real_buckets

def meature_result(real_buckets, BUCKETS, flag = False):
    buckets = []
    if not flag:
        for bucket in BUCKETS:
            tmp_bucket = []
            for stack in bucket:
                tmp_bucket.append(stack.id)
            buckets.append(tmp_bucket)
    else:
        buckets = BUCKETS
    
    N = 0.0
    for bucket in real_buckets:
        N += len(bucket)
    
    fmeasure = 0.0
    for i in range(0, len(real_buckets)):
        f = []
        for j in range(0, len(buckets)):
            Li_Cj = len(list(set(real_buckets[i]).intersection(set(buckets[j]))))
            precision = float(Li_Cj)/float(len(buckets[j]))
            recall = float(Li_Cj)/float(len(real_buckets[i]))
            if precision == 0 or recall == 0:
                f.append(0)
            else:
                f.append(float((2 * precision * recall) / (precision + recall)) )
        fmeasure += float(len(real_buckets[i])) * float(max(f)) / float(N)
    return fmeasure

def main():
    json_path = 'dataset/eclipse/df_eclipse.json'
    all_stacks = read_dataset(json_path)
    
    #---Training---
    train_num = 200
    c = 0.0
    c_best = 0.0
    c_max = 2.0

    dist = 0.0
    dist_best = 0.0
    dist_max = 1.0

    o = 0.0
    o_best = 0.0
    o_max = 2.0

    s = 0.01

    real_buckets = generate_realbuckets(all_stacks[0:train_num])
    fm_max = 0.0
    while dist < dist_max:
        rebuckets = rebucket.clustering(all_stacks[0:train_num], c, o ,dist)
        f_m = meature_result(real_buckets, rebuckets)
        if f_m > fm_max:
            fm_max = f_m
            dist_best = dist
        dist += s
    print "best dist is " + str(dist_best)

    fm_max = 0.0
    while o < o_max:
        rebuckets = rebucket.clustering(all_stacks[0:train_num], c, o ,dist_best)
        f_m = meature_result(real_buckets, rebuckets)
        if f_m > fm_max:
            fm_max = f_m
            o_best = o
        o += s
    print "best o is " + str(o_best)

    fm_max = 0.0
    while c < c_max:
        rebuckets = rebucket.clustering(all_stacks[0:train_num], c, o_best ,dist_best)
        f_m = meature_result(real_buckets, rebuckets)
        if f_m > fm_max:
            fm_max = f_m
            c_best = c
        c += s
    print "best c is " + str(c_best)
    #---Training End---

    test_num = 2000
    count = 0
    real_buckets = generate_realbuckets(all_stacks[0:test_num])
    print "testing"
    print meature_result(real_buckets, real_buckets, True)
    print "end testing"
    for stack in all_stacks:
        count += 1
        rebucket.single_pass_clustering(stack)
        if count % 10 == 0:
            print count
        if count == test_num:
            break
    
    print len(rebucket.BUCKETS)
    print meature_result(real_buckets, rebucket.BUCKETS)

    print "rebucket.clustering..."
    rebuckets = rebucket.clustering(all_stacks[0:test_num], c_best, o_best ,dist_best)
    print len(rebuckets)
    print meature_result(real_buckets, rebuckets)

    print "prefix match..."
    prefix_buckets = rebucket.prefix_match(all_stacks[0:test_num])
    print len(prefix_buckets)
    print meature_result(real_buckets, prefix_buckets)

    print "Test num "+str(test_num)
    print "real buckets " + str(len(real_buckets))

if __name__ == "__main__":
    main()