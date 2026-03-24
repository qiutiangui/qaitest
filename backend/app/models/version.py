"""
版本管理模型
"""
from tortoise import fields
from tortoise.models import Model


class ProjectVersion(Model):
    """项目版本表"""
    
    id = fields.IntField(pk=True, description="版本ID")
    project = fields.ForeignKeyField("models.Project", related_name="versions", description="所属项目")
    version_number = fields.CharField(max_length=20, description="版本号")
    version_name = fields.CharField(max_length=200, null=True, description="版本名称")
    description = fields.TextField(null=True, description="版本描述")
    status = fields.CharField(max_length=20, default="开发中", description="状态：开发中/测试中/已发布/已归档")
    release_notes = fields.TextField(null=True, description="发布说明")
    is_baseline = fields.BooleanField(default=False, description="是否为基线版本")
    created_by = fields.CharField(max_length=50, null=True, description="创建人")
    released_at = fields.DatetimeField(null=True, description="发布时间")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    
    class Meta:
        table = "project_versions"
        table_description = "项目版本表"
        unique_together = ("project", "version_number")
    
    def __str__(self):
        return f"ProjectVersion({self.id}, {self.version_number})"


class VersionSnapshot(Model):
    """版本快照表"""
    
    id = fields.IntField(pk=True, description="快照ID")
    version = fields.ForeignKeyField("models.ProjectVersion", related_name="snapshots", description="所属版本")
    snapshot_type = fields.CharField(max_length=50, description="快照类型：需求快照/用例快照/计划快照/报告快照")
    snapshot_data = fields.JSONField(description="快照数据")
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "version_snapshots"
        table_description = "版本快照表"
    
    def __str__(self):
        return f"VersionSnapshot({self.id}, {self.snapshot_type})"
