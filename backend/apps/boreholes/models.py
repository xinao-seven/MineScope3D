"""钻孔及分层数据库模型。"""
import uuid

from django.contrib.gis.db import models


class Borehole(models.Model):
	"""钻孔主表。"""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	borehole_code = models.CharField(max_length=120, unique=True)
	name = models.CharField(max_length=120)
	longitude = models.FloatField(default=0)
	latitude = models.FloatField(default=0)
	elevation = models.FloatField(default=0)
	depth_total = models.FloatField(default=0)
	workface_name = models.CharField(max_length=120, blank=True, default='')
	remark = models.TextField(blank=True, default='')
	geom = models.PointField(srid=4326, geography=True, null=True, blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('name',)

	def __str__(self) -> str:
		return f'{self.borehole_code} ({self.name})'


class BoreholeLayer(models.Model):
	"""钻孔分层明细表。"""

	id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
	borehole = models.ForeignKey(Borehole, on_delete=models.CASCADE, related_name='layers')
	layer_name = models.CharField(max_length=120)
	top_depth = models.FloatField(default=0)
	thickness = models.FloatField(default=0)
	bottom_depth = models.FloatField(default=0)
	color = models.CharField(max_length=20, default='#23d18b')
	sort_order = models.PositiveIntegerField(default=1)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('sort_order', 'created_at')
		constraints = [
			models.UniqueConstraint(fields=('borehole', 'sort_order'), name='uniq_borehole_layer_sort_order'),
		]

	def __str__(self) -> str:
		return f'{self.borehole.name}-{self.layer_name}'
