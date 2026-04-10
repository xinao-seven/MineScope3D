"""边界数据序列化器。"""
from rest_framework import serializers

from .models import BoundaryRegion


class BoundaryRegionSerializer(serializers.ModelSerializer):
	"""边界对象序列化。"""

	id = serializers.SerializerMethodField()
	coordinates = serializers.SerializerMethodField()

	class Meta:
		model = BoundaryRegion
		fields = (
			'id',
			'name',
			'type',
			'area',
			'perimeter',
			'borehole_count',
			'properties',
			'coordinates',
		)

	def get_id(self, obj: BoundaryRegion) -> str:
		return str(obj.id)

	def get_coordinates(self, obj: BoundaryRegion) -> list[list[float]]:
		if not obj.geom:
			return []
		geom = obj.geom
		if geom.geom_type == 'Polygon':
			return [[round(point[0], 8), round(point[1], 8)] for point in geom.coords[0]]
		if geom.geom_type == 'MultiPolygon':
			polygon = geom[0]
			return [[round(point[0], 8), round(point[1], 8)] for point in polygon.coords[0]]
		if geom.geom_type == 'LineString':
			return [[round(point[0], 8), round(point[1], 8)] for point in geom.coords]
		if geom.geom_type == 'MultiLineString':
			line = geom[0]
			return [[round(point[0], 8), round(point[1], 8)] for point in line.coords]
		return []
