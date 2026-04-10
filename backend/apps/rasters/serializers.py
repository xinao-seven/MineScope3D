"""专题图层序列化器。"""
from rest_framework import serializers

from .models import RasterLayer


class RasterLayerSerializer(serializers.ModelSerializer):
	"""专题图层对象序列化。"""

	id = serializers.SerializerMethodField()
	bounds = serializers.SerializerMethodField()

	class Meta:
		model = RasterLayer
		fields = (
			'id',
			'name',
			'type',
			'url',
			'bounds',
			'opacity',
			'legend_config',
			'description',
			'time_tag',
		)

	def get_id(self, obj: RasterLayer) -> str:
		return str(obj.id)

	def get_bounds(self, obj: RasterLayer) -> dict[str, float]:
		return {
			'west': obj.west,
			'south': obj.south,
			'east': obj.east,
			'north': obj.north,
		}
