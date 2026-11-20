import React, { useEffect, useRef } from 'react'
import L from 'leaflet'
import {
  getKpiFillColor,
  getKpiStrokeStyle,
  formatKpiDisplay,
  getStatusBadge,
  getQualityLevelName,
  COLORS,
} from '../utils/colorScale'

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

  // 2. Cập nhật hoặc vẽ lại Layer GeoJSON khi dữ liệu hoặc bộ lọc thay đổi
  useEffect(() => {
    const map = mapInstanceRef.current
    if (!map || !geoJsonData) return

    // Xóa layer cũ nếu có
    if (geoJsonLayerRef.current) {
      map.removeLayer(geoJsonLayerRef.current)
      geoJsonLayerRef.current = null
    }

    // Tính max traffic nếu đang chọn kpi traffic
    let maxTraffic = 100
    if (kpiMeta?.kpi_code === 'traffic' && kpiItemsMap) {
      Object.values(kpiItemsMap).forEach((item) => {
        if (item?.value && item.value > maxTraffic) maxTraffic = item.value
      })
    }

    // Hàm lấy style cho từng polygon vùng
    const styleFeature = (feature) => {
      const code = feature.properties?.region_code
      const item = kpiItemsMap?.[code]

      const strokeStyle = getKpiStrokeStyle(item)
      const fillColor = getKpiFillColor(item, kpiMeta, maxTraffic)

      return {
        fillColor,
        fillOpacity: 0.72,
        weight: strokeStyle.weight,
        color: strokeStyle.color,
        dashArray: strokeStyle.dashArray,
      }
    }

    // Hàm gắn sự kiện cho từng feature
    const onEachFeature = (feature, layer) => {
      const props = feature.properties || {}
      const code = props.region_code
      const name = props.region_name
      const item = kpiItemsMap?.[code]

      const formattedVal = formatKpiDisplay(item, kpiMeta)
      const badge = getStatusBadge(item)
      const qualityName = getQualityLevelName(item, kpiMeta)

      // Tạo nội dung Tooltip hover
      const tooltipContent = `
        <div class="map-tooltip">
          <div class="tooltip-title"><strong>${name}</strong> <span class="tooltip-code">(${code})</span></div>
          <div class="tooltip-row">
            <span>Giá trị:</span>
            <strong class="tooltip-val">${formattedVal}</strong>
          </div>
          ${
            item && item.value !== null && kpiMeta?.kpi_code !== 'traffic'
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
          <div class="tooltip-hint">👉 Nhấp để xem biểu đồ chuỗi thời gian</div>
          ${
            level === 'province' && code === '79'
              ? `<div class="tooltip-drilldown">🔍 Nhấp để xem 168 phường/xã TP.HCM</div>`
              : ''
          }
        </div>
      `

      layer.bindTooltip(tooltipContent, {
        sticky: true,
        className: 'custom-leaflet-tooltip',
        direction: 'auto',
      })

      // Sự kiện hover & click
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
          // Mở modal biểu đồ chi tiết vùng
          onSelectRegion(feature)
        },
      })
    }

    // Tạo GeoJSON layer mới
    const geoJsonLayer = L.geoJSON(geoJsonData, {
      style: styleFeature,
      onEachFeature,
    }).addTo(map)

    geoJsonLayerRef.current = geoJsonLayer

    // Tự động căn chỉnh bounds bản đồ
    try {
      const bounds = geoJsonLayer.getBounds()
      if (bounds.isValid()) {
        map.fitBounds(bounds, { padding: [20, 20], maxZoom: level === 'ward' ? 13 : 8 })
      }
    } catch (e) {
      console.warn('Không thể fitBounds:', e)
    }
  }, [geoJsonData, kpiItemsMap, kpiMeta, level, onSelectRegion])

  return (
    <div className="map-view-wrapper">
      {/* Nút Breadcrumb quay lại khi đang xem cấp phường */}
      {level === 'ward' && (
        <div className="map-nav-overlay">
          <button className="btn-back-province" onClick={onBackToProvince}>
            ⬅ Quay lại cấp Tỉnh / Thành phố (34 vùng)
          </button>
          <span className="current-view-badge">Đang xem: 168 Phường / Xã TP.HCM</span>
        </div>
      )}

      {/* Container bản đồ Leaflet */}
      <div id="map-container" ref={mapContainerRef} className="leaflet-map-container" />
    </div>
  )
}
