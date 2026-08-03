import math

class CoordinateConverter:
    """
    坐标转换工具类，支持WGS84、GCJ02和BD09三种坐标系统之间的互相转换
    """
    
    def __init__(self):
        self.x_pi = 3.14159265358979324 * 3000.0 / 180.0
        self.pi = 3.1415926535897932384626  # π
        self.a = 6378245.0  # 长半轴
        self.ee = 0.00669342162296594323  # 偏心率平方
    
    def convert(self, lng, lat, from_type, to_type):
        """
        坐标转换主函数
        :param lng: 经度
        :param lat: 纬度
        :param from_type: 源坐标类型
        :param to_type: 目标坐标类型
        :return: 转换后的经纬度
        """
        if from_type == to_type:
            return lng, lat
        
        # 先转换为WGS84
        if from_type == 'GCJ02':
            lng, lat = self.gcj02_to_wgs84(lng, lat)
        elif from_type == 'BD09':
            lng, lat = self.bd09_to_wgs84(lng, lat)
        
        # 再从WGS84转换为目标坐标系
        if to_type == 'GCJ02':
            lng, lat = self.wgs84_to_gcj02(lng, lat)
        elif to_type == 'BD09':
            lng, lat = self.wgs84_to_bd09(lng, lat)
        
        return lng, lat
    
    def out_of_china(self, lng, lat):
        """
        判断是否在中国境外
        :param lng: 经度
        :param lat: 纬度
        :return: 是否在中国境外
        """
        return not (73.66 < lng < 135.05 and 3.86 < lat < 53.55)
    
    def wgs84_to_gcj02(self, lng, lat):
        """
        WGS84坐标系转GCJ02坐标系
        :param lng: WGS84坐标系下的经度
        :param lat: WGS84坐标系下的纬度
        :return: GCJ02坐标系下的经度、纬度
        """
        if self.out_of_china(lng, lat):
            return lng, lat
        
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return mglng, mglat
    
    def gcj02_to_wgs84(self, lng, lat):
        """
        GCJ02坐标系转WGS84坐标系
        :param lng: GCJ02坐标系下的经度
        :param lat: GCJ02坐标系下的纬度
        :return: WGS84坐标系下的经度、纬度
        """
        if self.out_of_china(lng, lat):
            return lng, lat
        
        dlat = self._transformlat(lng - 105.0, lat - 35.0)
        dlng = self._transformlng(lng - 105.0, lat - 35.0)
        radlat = lat / 180.0 * self.pi
        magic = math.sin(radlat)
        magic = 1 - self.ee * magic * magic
        sqrtmagic = math.sqrt(magic)
        dlat = (dlat * 180.0) / ((self.a * (1 - self.ee)) / (magic * sqrtmagic) * self.pi)
        dlng = (dlng * 180.0) / (self.a / sqrtmagic * math.cos(radlat) * self.pi)
        mglat = lat + dlat
        mglng = lng + dlng
        return lng * 2 - mglng, lat * 2 - mglat
    
    def bd09_to_gcj02(self, lng, lat):
        """
        BD09坐标系转GCJ02坐标系
        :param lng: BD09坐标系下的经度
        :param lat: BD09坐标系下的纬度
        :return: GCJ02坐标系下的经度、纬度
        """
        x = lng - 0.0065
        y = lat - 0.006
        z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * self.x_pi)
        theta = math.atan2(y, x) - 0.000003 * math.cos(x * self.x_pi)
        gg_lng = z * math.cos(theta)
        gg_lat = z * math.sin(theta)
        return gg_lng, gg_lat
    
    def gcj02_to_bd09(self, lng, lat):
        """
        GCJ02坐标系转BD09坐标系
        :param lng: GCJ02坐标系下的经度
        :param lat: GCJ02坐标系下的纬度
        :return: BD09坐标系下的经度、纬度
        """
        z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * self.x_pi)
        theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * self.x_pi)
        bd_lng = z * math.cos(theta) + 0.0065
        bd_lat = z * math.sin(theta) + 0.006
        return bd_lng, bd_lat
    
    def wgs84_to_bd09(self, lng, lat):
        """
        WGS84坐标系转BD09坐标系
        :param lng: WGS84坐标系下的经度
        :param lat: WGS84坐标系下的纬度
        :return: BD09坐标系下的经度、纬度
        """
        lng, lat = self.wgs84_to_gcj02(lng, lat)
        return self.gcj02_to_bd09(lng, lat)
    
    def bd09_to_wgs84(self, lng, lat):
        """
        BD09坐标系转WGS84坐标系
        :param lng: BD09坐标系下的经度
        :param lat: BD09坐标系下的纬度
        :return: WGS84坐标系下的经度、纬度
        """
        lng, lat = self.bd09_to_gcj02(lng, lat)
        return self.gcj02_to_wgs84(lng, lat)
    
    def _transformlat(self, lng, lat):
        """
        经度转换辅助函数
        """
        ret = -100.0 + 2.0 * lng + 3.0 * lat + 0.2 * lat * lat + 0.1 * lng * lat + 0.2 * math.sqrt(abs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 * math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lat * self.pi) + 40.0 * math.sin(lat / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (160.0 * math.sin(lat / 12.0 * self.pi) + 320 * math.sin(lat * self.pi / 30.0)) * 2.0 / 3.0
        return ret
    
    def _transformlng(self, lng, lat):
        """
        纬度转换辅助函数
        """
        ret = 300.0 + lng + 2.0 * lat + 0.1 * lng * lng + 0.1 * lng * lat + 0.1 * math.sqrt(abs(lng))
        ret += (20.0 * math.sin(6.0 * lng * self.pi) + 20.0 * math.sin(2.0 * lng * self.pi)) * 2.0 / 3.0
        ret += (20.0 * math.sin(lng * self.pi) + 40.0 * math.sin(lng / 3.0 * self.pi)) * 2.0 / 3.0
        ret += (150.0 * math.sin(lng / 12.0 * self.pi) + 300.0 * math.sin(lng / 30.0 * self.pi)) * 2.0 / 3.0
        return ret 