"""专题图层数据库模型。"""
import uuid

from django.contrib.gis.db import models


class RasterLayer(models.Model):
	"""TIFF 导入后的专题图层元信息。"""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=120, unique=True)
	type = models.CharField(max_length=80, default='subsidence')
	url = models.CharField(max_length=255, blank=True, default='')
	opacity = models.FloatField(default=0.62)
	legend_config = models.JSONField(default=list, blank=True)
	description = models.TextField(blank=True, default='')
	time_tag = models.CharField(max_length=120, blank=True, default='')
	source_crs = models.CharField(max_length=120, blank=True, default='')
	bounds = models.PolygonField(srid=4326, null=True, blank=True)
	west = models.FloatField(default=0)
	south = models.FloatField(default=0)
	east = models.FloatField(default=0)
	north = models.FloatField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('name',)

	def __str__(self) -> str:
		return self.name
