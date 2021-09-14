class SharedInfo(object):
    def __init__(self):
        self.name = ''
        self.ggl_proxies_num = 0
        self.tot_proxies_num = 0
        self.non_proxies_num = 0
        
        self.ggl_tot_cnt = 0
        self.ggl_last_time = 0.0
        self.ggl_avg_time = 0.0
        self.ggl_cnt = 0
        self.ggl_obj_changed_cnt = 0
        self.ggl_tot_time = 0.0
        
        self.baidu_tot_cnt = 0
        self.baidu_last_time = 0.0
        self.baidu_avg_time = 0.0
        self.baidu_cnt = 0
        self.baidu_obj_changed_cnt = 0
        self.baidu_tot_time = 0.0
        
        self.xiaoniu_tot_cnt = 0
        self.xiaoniu_last_time = 0.0
        self.xiaoniu_avg_time = 0.0
        self.xiaoniu_cnt = 0
        self.xiaoniu_obj_changed_cnt = 0
        self.xiaoniu_tot_time = 0.0
        
    def __str__(self):
        report = """
====================================================================================================
                                            REPORT - {}\n
====================================================================================================
          Process - Last Time (s) - AVG Time (s) - Remain Time (s) - Changed Num - Proxies Num
Google  | {}/{} ({:.2f}%) - {:.2f} - {:.2f} - {:.2f} - {}\n
Baidu   | {}/{} ({:.2f}%) - {:.2f} - {:.2f} - {:.2f} - {}\n
Xiaoniu | {}/{} ({:.2f}%) - {:.2f} - {:.2f} - {:.2f} - {}\n
====================================================================================================
"""
        rstring = report.format(self.name,
                                self.ggl_cnt, self.ggl_tot_cnt, self.ggl_cnt/self.ggl_tot_cnt*100, 
                                    self.ggl_last_time, self.ggl_avg_time, self.ggl_avg_time*(self.ggl_tot_cnt - self.ggl_cnt),
                                    self.ggl_obj_changed_cnt,
                                self.baidu_cnt, self.baidu_tot_cnt, self.baidu_cnt/self.baidu_tot_cnt*100, 
                                    self.baidu_last_time, self.baidu_avg_time, self.baidu_avg_time*(self.baidu_tot_cnt - self.baidu_cnt),
                                    self.baidu_obj_changed_cnt,
                                self.xiaoniu_cnt, self.xiaoniu_tot_cnt, self.xiaoniu_cnt/self.xiaoniu_tot_cnt*100, 
                                    self.xiaoniu_last_time, self.xiaoniu_avg_time, self.xiaoniu_avg_time*(self.xiaoniu_tot_cnt - self.xiaoniu_cnt),
                                    self.xiaoniu_obj_changed_cnt)
        return rstring
    
    def report(self):
        print(self)
