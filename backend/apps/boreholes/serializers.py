"""钻孔数据序列化器。"""
from rest_framework import serializers

from .models import Borehole, BoreholeLayer


class BoreholeLayerSerializer(serializers.ModelSerializer):
	"""钻孔分层序列化。"""

	id = serializers.SerializerMethodField()

	class Meta:
		model = BoreholeLayer
		fields = ('id', 'layer_name', 'top_depth', 'thickness', 'bottom_depth', 'color', 'sort_order')

	def get_id(self, obj: BoreholeLayer) -> str:
		return str(obj.id)


class BoreholeSerializer(serializers.ModelSerializer):
	"""钻孔主数据序列化。"""

	id = serializers.SerializerMethodField()
	layers = BoreholeLayerSerializer(many=True, read_only=True)

	class Meta:
		model = Borehole
		fields = (
			'id',
			'borehole_code',
			'name',
			'longitude',
			'latitude',
			'elevation',
			'depth_total',
			'workface_name',
			'remark',
			'layers',
		)

	def get_id(self, obj: Borehole) -> str:
		return str(obj.id)
