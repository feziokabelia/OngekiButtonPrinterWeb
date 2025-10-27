from django.db import models


class ButtonConfig(models.Model):
    """
    按钮配置表 - 只包含最核心的字段
    """

    # 按钮标识（主键）
    button_key = models.CharField(
        max_length=20,
        primary_key=True,
        verbose_name="按钮键值"
    )

    # 图片文件名
    image_name = models.CharField(
        max_length=100,
        verbose_name="图片文件名"
    )

    # 图片路径
    image_path = models.CharField(
        max_length=200,
        default="images/buttons/",
        verbose_name="图片路径"
    )

    class Meta:
        db_table = 'button_config'
        verbose_name = '按钮配置'
        verbose_name_plural = '按钮配置'

    def __str__(self):
        return f"{self.button_key}"

    @property
    def full_image_path(self):
        """获取完整的图片URL路径"""
        return f"/static/{self.image_path}/{self.image_name}"