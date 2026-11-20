import React, { useState, useEffect, useMemo } from 'react'
import FilterBar from './components/FilterBar'
import MapView from './components/MapView'
import Legend from './components/Legend'
import RegionModal from './components/RegionModal'
import { fetchKpis, fetchSources, fetchRegions, fetchKpiValues } from './api/client'
import './App.css'

export default function App() {
  // Dữ liệu danh mục
  const [kpis, setKpis] = useState([])
  const [sources, setSources] = useState([])
  const [selectedKpi, setSelectedKpi] = useState('cssr')
  const [selectedSource, setSelectedSource] = useState('BE-SAMPLE')

  // Trạng thái bộ lọc
  const [level, setLevel] = useState('province') // 'province' | 'ward'
  const [periodType, setPeriodType] = useState('hour') // 'hour' | 'day'
  const [at, setAt] = useState('2026-10-02T10:00') // Mốc thời gian mẫu

  // Dữ liệu hiển thị bản đồ
  const [geoJsonData, setGeoJsonData] = useState(null)
  const [kpiResponse, setKpiResponse] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // Vùng được chọn để xem biểu đồ chi tiết
  const [selectedRegion, setSelectedRegion] = useState(null)

  // 1. Tải danh mục KPI và danh sách Nguồn khi khởi động
  useEffect(() => {
    Promise.all([fetchKpis(), fetchSources()])
      .then(([kpiList, sourceList]) => {
        setKpis(kpiList)
        setSources(sourceList)

        if (kpiList.length > 0 && !selectedKpi) {
          setSelectedKpi(kpiList[0].kpi_code)
        }

        // Ưu tiên chọn nguồn BE-SAMPLE cho Issue #5
        const beSample = sourceList.find((s) => s.source_code === 'BE-SAMPLE')
        if (beSample) {
          setSelectedSource('BE-SAMPLE')
        } else if (sourceList.length > 0) {
          setSelectedSource(sourceList[0].source_code)
        }
      })
      .catch((err) => {
        console.error('Lỗi khởi tạo:', err)
        setError('Không thể kết nối đến Backend: ' + err.message)
      })
  }, [])

  // 2. Tải GeoJSON khi thay đổi cấp hành chính (tỉnh <-> phường)
  useEffect(() => {
    let isMounted = true
    setLoading(true)

    fetchRegions(level, 0.001)
      .then((data) => {
        if (!isMounted) return
        setGeoJsonData(data)
        setLoading(false)
      })
      .catch((err) => {
        if (!isMounted) return
        console.error('Lỗi tải GeoJSON:', err)
        setError(`Lỗi tải ranh giới ${level}: ${err.message}`)
        setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [level])

  // 3. Tải giá trị KPI khi bộ lọc thay đổi
  useEffect(() => {
    if (!selectedKpi || !at || !selectedSource) return

    let isMounted = true
    setLoading(true)
    setError(null)

    // Chuẩn hóa định dạng `at`: ngày YYYY-MM-DD, giờ YYYY-MM-DDTHH:00
    const cleanAt =
      periodType === 'day'
        ? at.substring(0, 10)
        : at.length === 16
        ? `${at.substring(0, 13)}:00`
        : at

    fetchKpiValues({
      kpi: selectedKpi,
      at: cleanAt,
      level,
      periodType,
      source: selectedSource,
    })
      .then((res) => {
        if (!isMounted) return
        setKpiResponse(res)
        setLoading(false)
      })
      .catch((err) => {
        if (!isMounted) return
        console.error('Lỗi tải KPI values:', err)
        setError(`Lỗi tải số liệu: ${err.message}`)
        setLoading(false)
      })

    return () => {
      isMounted = false
    }
  }, [selectedKpi, at, level, periodType, selectedSource])

  // Tạo map tra cứu nhanh region_code -> item
  const kpiItemsMap = useMemo(() => {
    if (!kpiResponse?.items) return {}
    const map = {}
    for (const item of kpiResponse.items) {
      map[item.region_code] = item
    }
    return map
  }, [kpiResponse])

  // Thông tin KPI hiện tại
  const currentKpiMeta = useMemo(() => {
    return kpis.find((k) => k.kpi_code === selectedKpi) || kpiResponse?.kpi
  }, [kpis, selectedKpi, kpiResponse])

  // Lấy thời gian cập nhật gần nhất từ dữ liệu items
  const latestUpdatedAt = useMemo(() => {
    if (!kpiResponse?.items?.length) return null
    return kpiResponse.items[0]?.updated_at
  }, [kpiResponse])

  // Nguồn dữ liệu hiện tại
  const currentSourceMeta = useMemo(() => {
    return sources.find((s) => s.source_code === selectedSource) || kpiResponse?.source
  }, [sources, selectedSource, kpiResponse])

  // Xử lý chuyển đổi loại chu kỳ (giờ/ngày)
  const handleChangePeriodType = (newType) => {
    setPeriodType(newType)
    if (newType === 'day' && at.includes('T')) {
      setAt(at.substring(0, 10))
    } else if (newType === 'hour' && !at.includes('T')) {
      setAt(`${at}T10:00`)
    }
  }

  return (
    <div className="app-container">
      {/* Thanh công cụ lọc */}
      <FilterBar
        kpis={kpis}
        selectedKpi={selectedKpi}
        onSelectKpi={setSelectedKpi}
        level={level}
        onChangeLevel={setLevel}
        periodType={periodType}
        onChangePeriodType={handleChangePeriodType}
        at={at}
        onChangeAt={setAt}
        sources={sources}
        selectedSource={selectedSource}
        onChangeSource={setSelectedSource}
        loading={loading}
      />

      {/* Thông báo lỗi nếu có */}
      {error && (
        <div className="error-banner">
          <span>⚠️ {error}</span>
          <button className="error-close-btn" onClick={() => setError(null)}>
            ✕
          </button>
        </div>
      )}

      {/* Khu vực Bản đồ + Chú giải */}
      <main className="main-content">
        <MapView
          geoJsonData={geoJsonData}
          kpiItemsMap={kpiItemsMap}
          kpiMeta={currentKpiMeta}
          level={level}
          onSelectRegion={setSelectedRegion}
          onBackToProvince={() => setLevel('province')}
        />

        {/* Chú giải góc bản đồ (thỏa mãn tiêu chí nghiệm thu) */}
        <Legend
          kpiMeta={currentKpiMeta}
          periodAt={kpiResponse?.period?.at || at}
          updatedAt={latestUpdatedAt}
          sourceMeta={currentSourceMeta}
        />
      </main>

      {/* Modal biểu đồ chuỗi thời gian khi click vùng */}
      {selectedRegion && (
        <RegionModal
          region={selectedRegion}
          kpiList={kpis}
          currentKpi={selectedKpi}
          currentPeriodType={periodType}
          currentSource={selectedSource}
          onClose={() => setSelectedRegion(null)}
        />
      )}
    </div>
  )
}
