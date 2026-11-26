import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import {
  getKpiFillColor,
  getKpiStrokeStyle,
  formatKpiDisplay,
  getStatusBadge,
  getQualityLevelName,
  isQualityKpi,
  COLORS,
} from '../utils/colorScale'

function buildTooltipHtml(feature, item, kpiMeta, level) {
  const props = feature.properties || {}
  const code = props.region_code
  const name = props.region_name

  const formattedVal = formatKpiDisplay(item, kpiMeta)
  const badge = getStatusBadge(item)
  const qualityName = getQualityLevelName(item, kpiMeta)

  return `
    <div class="map-tooltip">
      <div class="tooltip-title"><strong>${name}</strong> <span class="tooltip-code">(${code})</span></div>
      <div class="tooltip-row">
        <span>Giá trị:</span>
        <strong class="tooltip-val">${formattedVal}</strong>
      </div>
      ${
        item && item.value !== null && isQualityKpi(kpiMeta) && qualityName
          ? `<div class="tooltip-row">
              <span>Chất lượng:</span>
              <span class="badge" style="background:${getKpiFillColor(item, kpiMeta)}">${qualityName}</span>
            </div>`
          : ''
      }
      <div class="tooltip-row">
        <span>Trạng thái:</span>
        <span class="tooltip-status" style="color:${badge.color}">● ${badge.label}</span>
      </div>
      ${
        item?.reason === 'no_positive_traffic'
          ? `<div class="tooltip-warning">⚠️ Vùng không có lưu lượng, không tính được trung bình trọng số</div>`
          : ''
      }
      ${
        item?.status === 'partial'
          ? `<div class="tooltip-warning">⚠️ Thiếu một phần cell trong kỳ báo cáo (viền nét đứt)</div>`
          : ''
      }
      ${
        level === 'province' && code === '79'
          ? `<div class="tooltip-drilldown">🔍 Nhấp để xem 168 phường/xã TP.HCM</div>`
          : `<div class="tooltip-hint">👉 Nhấp để xem biểu đồ chuỗi thời gian</div>`
      }
    </div>
  `
}

export default function MapView({
  geoJsonData,
  kpiItemsMap,
  kpiMeta,
  level,
  onSelectRegion,
  onDrillDownWard,
  onBackToProvince,
}) {
  const mapContainerRef = useRef(null)
  const mapInstanceRef = useRef(null)
  const geoJsonLayerRef = useRef(null)

  // Lưu giá trị mới nhất trong ref để tránh stale closure và giữ nguyên góc nhìn khi đổi KPI/giờ
  const kpiMapRef = useRef(kpiItemsMap)
  const kpiMetaRef = useRef(kpiMeta)
  const levelRef = useRef(level)
  const onSelectRegionRef = useRef(onSelectRegion)
  const onDrillDownWardRef = useRef(onDrillDownWard)

  useEffect(() => {
    onSelectRegionRef.current = onSelectRegion
    onDrillDownWardRef.current = onDrillDownWard
  }, [onSelectRegion, onDrillDownWard])

  // 1. Khởi tạo Leaflet Map (chỉ chạy 1 lần khi mount)
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) return

    const map = L.map(mapContainerRef.current, {
      center: [16.0, 106.0],
      zoom: 6,
      minZoom: 5,
      maxZoom: 18,
    })

    // Lớp nền OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> | Ranh giới: <a href="https://sapnhap.bando.com.vn" target="_blank">sapnhap.bando.com.vn (Bộ NN&MT)</a>, CC BY-NC 4.0',
    }).addTo(map)

    mapInstanceRef.current = map

    return () => {
      map.remove()
      mapInstanceRef.current = null
    }
  }, [])

  // 2. Effect 1: Chỉ chạy khi geoJsonData hoặc level thay đổi để dựng lại layer và fitBounds
  useEffect(() => {
    const map = mapInstanceRef.current
    levelRef.current = level
    if (!map || !geoJsonData) return

    if (geoJsonLayerRef.current) {
      map.removeLayer(geoJsonLayerRef.current)
      geoJsonLayerRef.current = null
    }

    const styleFeature = (feature) => {
      const code = feature.properties?.region_code
      const item = kpiMapRef.current?.[code]
      const strokeStyle = getKpiStrokeStyle(item)
      const fillColor = getKpiFillColor(item, kpiMetaRef.current)

      return {
        fillColor,
        fillOpacity: 0.72,
        weight: strokeStyle.weight,
        color: strokeStyle.color,
        dashArray: strokeStyle.dashArray,
      }
    }

    const onEachFeature = (feature, layer) => {
      const code = feature.properties?.region_code

      // Hàm tooltip động luôn đọc từ ref để phản ánh dữ liệu KPI mới nhất
      layer.bindTooltip(
        () =>
          buildTooltipHtml(
            feature,
            kpiMapRef.current?.[code],
            kpiMetaRef.current,
            levelRef.current
          ),
        {
          sticky: true,
          className: 'custom-leaflet-tooltip',
          direction: 'auto',
        }
      )

      layer.on({
        mouseover: (e) => {
          const l = e.target
          l.setStyle({
            weight: 3,
            color: COLORS.highlight,
            fillOpacity: 0.88,
          })
          if (!L.Browser.ie && !L.Browser.opera && !L.Browser.edge) {
            l.bringToFront()
          }
        },
        mouseout: (e) => {
          geoJsonLayerRef.current?.resetStyle(e.target)
        },
        click: () => {
          // Khi ở cấp tỉnh và click vào TP.HCM ('79') -> drill-down sang 168 phường/xã
          if (levelRef.current === 'province' && code === '79') {
            onDrillDownWardRef.current?.()
            return
          }
          onSelectRegionRef.current?.(feature)
        },
      })
    }

    const geoJsonLayer = L.geoJSON(geoJsonData, {
      style: styleFeature,
      onEachFeature,
    }).addTo(map)

    geoJsonLayerRef.current = geoJsonLayer

    try {
      const bounds = geoJsonLayer.getBounds()
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20], maxZoom: level === 'ward' ? 13 : 8 })
      }
    } catch (e) {
      console.warn('Không thể fitBounds:', e)
    }
  }, [geoJsonData, level])

  // 3. Effect 2: Chỉ cập nhật màu, viền và tooltip trên layer hiện có khi KPI/giờ thay đổi
  useEffect(() => {
    kpiMapRef.current = kpiItemsMap
    kpiMetaRef.current = kpiMeta

    const geoJsonLayer = geoJsonLayerRef.current
    if (!geoJsonLayer) return

    geoJsonLayer.setStyle((feature) => {
      const code = feature.properties?.region_code
      const item = kpiItemsMap?.[code]
      const strokeStyle = getKpiStrokeStyle(item)
      const fillColor = getKpiFillColor(item, kpiMeta)

      return {
        fillColor,
        fillOpacity: 0.72,
        weight: strokeStyle.weight,
        color: strokeStyle.color,
        dashArray: strokeStyle.dashArray,
      }
    })

    // Cập nhật nội dung nếu tooltip đang mở
    geoJsonLayer.eachLayer((layer) => {
      if (layer.getTooltip?.() && layer.isTooltipOpen?.()) {
        layer.getTooltip().update()
      }
    })
  }, [kpiItemsMap, kpiMeta])

  const handleOpenHcmChart = () => {
    const hcmFeature =
      level === 'province'
        ? geoJsonData?.features?.find((f) => f.properties?.region_code === '79')
        : null

    onSelectRegion(
      hcmFeature || {
        properties: {
          region_code: '79',
          region_name: 'Thành phố Hồ Chí Minh',
          region_level: 'province',
          parent_code: null,
        },
      }
    )
  }

  return (
    <div className="map-view-wrapper">
      {/* Thanh điều hướng góc trên trái: xem biểu đồ TP.HCM cấp tỉnh & quay lại từ cấp phường */}
      <div className="map-nav-overlay">
        {level === 'ward' && (
          <>
            <button className="btn-back-province" onClick={onBackToProvince}>
              ⬅ Quay lại cấp Tỉnh / Thành phố (34 vùng)
            </button>
            <span className="current-view-badge">Đang xem: 168 Phường / Xã TP.HCM</span>
          </>
        )}
        <button
          className="btn-hcm-chart"
          onClick={handleOpenHcmChart}
          title="Xem biểu đồ chuỗi thời gian toàn TP.HCM (mã 79)"
        >
          📊 Biểu đồ TP.HCM
        </button>
      </div>

      {/* Container bản đồ Leaflet */}
      <div id="map-container" ref={mapContainerRef} className="leaflet-map-container" />
    </div>
  )
}
