#include "rebucket.h"
#include "rapidjson/document.h"
#include "rapidjson/writer.h"
#include "rapidjson/stringbuffer.h"
#include <cmath>
#include <algorithm>
#include <vector>
#include <omp.h>
using namespace rapidjson;
//TODO It should in redis
vector<Bucket> buckets;
std::string sconvert(const char *pCh, int arraySize){
  std::string str;
  if (pCh[arraySize-1] == '\0') str.append(pCh);
  else for(int i=0; i<arraySize; i++) str.append(1,pCh[i]);
  return str;
}
Stack json_to_stack(const char* json)
{
    Stack stack;
    Document d;
    d.Parse(json);
    
    stack.stack_id = sconvert(d["stack_id"].GetString(), d["stack_id"].GetStringLength());
    for (int i = 0; i < d["stack_arr"].GetArray().Size(); ++i) {
        stack.frames.push_back(d["stack_arr"].GetArray()[i].GetString());
    }
    return stack;
}

double get_dist(Stack stack1, Stack stack2)
{
    double c = 0.04;
    double o = 0.13;
    int stack_len1 = stack1.frames.size();
    int stack_len2 = stack2.frames.size();
    if(stack_len1 == 1 || stack_len2 == 1) {
        return 1.0;
    }
    //FIXME not good enough
    std::vector<std::vector<double> > M(stack_len1 + 1, std::vector<double>(stack_len2 + 1));

    for(int i = 1; i < stack_len1 + 1; ++i){
        for(int j = 1; j < stack_len2 + 1; ++j) {
            double x = 0;
            if(stack1.frames[i - 1] == stack2.frames[j - 1]){
                x = exp(-c*min(i-1, j-1)) * exp(-o*abs(i-j));
            }
            M[i][j] = max(max(M[i-1][j-1] + x, M[i-1][j]), M[i][j-1]);
        }
    }
    double sig = 0;
    for (int i = 0; i < min(stack_len1, stack_len2); ++i){
        sig += exp(-c * i);
    }
    double sim = M[stack_len1][stack_len2] / sig;
    return 1.0 - sim;

}

const char* single_pass_clustering(const char* stack_json)
{
    Stack stack = json_to_stack(stack_json);
    double min_dist = 2;
    int min_index = -1;
    #pragma omp parallel for
    for (int i = 0; i < buckets.size(); ++i){
        double dist = get_dist(stack, buckets[i].stacks[0]);
        if(dist < min_dist){
            min_dist = dist;
            min_index = i;
        }
    }
    string bucket_id = stack.stack_id;
    
    if (min_dist < 0.06) {
        buckets[min_index].stacks.push_back(stack);
        bucket_id = buckets[min_index].bucket_id;
    }
    else {
        Bucket bucket;
        bucket.bucket_id = stack.stack_id;
        bucket.stacks.push_back(stack);
        buckets.push_back(bucket);
    }
    //NOTE be careful
    static string s = bucket_id;
    s = bucket_id;
    return s.c_str();
}
void free_buffer(const char* str_ptr)
{
    if(!str_ptr) {
        return;
    }
    delete [] str_ptr;
}