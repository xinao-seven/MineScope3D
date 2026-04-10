"""边界数据库模型。"""
import uuid

from django.contrib.gis.db import models


class BoundaryRegion(models.Model):
	"""矿区与工作面边界对象。"""

	TYPE_MINE = 'mine'
	TYPE_WORKFACE = 'workface'
	TYPE_REGION = 'region'
	TYPE_CHOICES = (
		(TYPE_MINE, 'mine'),
		(TYPE_WORKFACE, 'workface'),
		(TYPE_REGION, 'region'),
	)

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	name = models.CharField(max_length=120)
	type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_REGION)
	area = models.FloatField(default=0)
	perimeter = models.FloatField(default=0)
	borehole_count = models.PositiveIntegerField(default=0)
	properties = models.JSONField(default=dict, blank=True)
	geom = models.GeometryField(srid=4326)
	source = models.CharField(max_length=120, blank=True, default='')
	source_crs = models.CharField(max_length=120, blank=True, default='')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('type', 'name')

	def __str__(self) -> str:
		return f'{self.name} ({self.type})'
