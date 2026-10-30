from django.db import models

class CommentResult(models.Model):
    # 실제 종목 명
    stock_name = models.CharField(max_length=100)
    # 원본 댓글 목록
    raw_comments = models.JSONField(default=list)
    # 정제 댓글 목록
    cleaned_comments = models.JSONField(default=list)
    # 증강 댓글 목록
    augmented_comments = models.JSONField(default=list)
    # IQR 하한
    iqr_lower = models.FloatField(null= True, blank=True)
    # IQR 상한
    iqr_upper = models.FloatField(null=True, blank=True)
    # 생성 일시
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.stock_name} ({self.created_at:%Y-%m-%d %H:%M})'