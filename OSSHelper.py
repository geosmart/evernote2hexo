
class OSSHelper():
    def oss_get(self, key="Blog/消息中间件之Kafka/kafka.jpg"):
        """
        生成public链接
        Args:
            key:

        Returns:

        """
        import oss2
        url = 'http://geosmart.oss-cn-shanghai.aliyuncs.com/Blog/{}'.format(key)
        return url

    def oss_update(self, key, local_file):
        """
        将本地文件上传到OSS
        Args:
            key:
            local_file:

        Returns:

        """
        import oss2
        endpoint = 'oss-cn-shanghai.aliyuncs.com'
        auth = oss2.Auth('LTAIJodCavPxCcxR', 'IOR5leQEewWhPaEerOpA6oysHZqgLE')
        bucket = oss2.Bucket(auth, endpoint, 'geosmart')
        # Bucket中的文件名（key）为story.txt
        # 上传
        print("upload {}".format(key))
        with open(u"{}".format(local_file), 'rb') as f:
            bucket.put_object("Blog/{}".format(key), f)
        return self.oss_get(key)

