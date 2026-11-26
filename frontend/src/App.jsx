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

  // Dữ liệu hiển thị bản đồ & trạng thái tải/lỗi tách riêng
  const [geoJsonState, setGeoJsonState] = useState({ level: null, data: null })
  const [loadingGeoJson, setLoadingGeoJson] = useState(true)
  const [geoJsonError, setGeoJsonError] = useState(null)

  const [kpiResponse, setKpiResponse] = useState(null)
  const [loadingKpi, setLoadingKpi] = useState(true)
  const [kpiError, setKpiError] = useState(null)

  const [initError, setInitError] = useState(null)

  // Vùng được chọn để xem biểu đồ chi tiết
  const [selectedRegion, setSelectedRegion] = useState(null)

  const isLoading = loadingGeoJson || loadingKpi
  const geoJsonData = geoJsonState.level === level ? geoJsonState.data : null
  const errorMessages = [initError, geoJsonError, kpiError].filter(Boolean)

  // 1. Tải danh mục KPI và danh sách Nguồn khi khởi động
  useEffect(() => {
    let isMounted = true

    Promise.all([fetchKpis(), fetchSources()])
      .then(([kpiList, sourceList]) => {
        if (!isMounted) return
        setKpis(kpiList)
        setSources(sourceList)
        setInitError(null)

        if (kpiList.length > 0) {
          setSelectedKpi((prev) =>
            kpiList.some((k) => k.kpi_code === prev) ? prev : kpiList[0].kpi_code
          )
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
        if (!isMounted) return
        console.error('Lỗi khởi tạo:', err)
        setInitError('Không thể kết nối đến Backend: ' + err.message)
      })

    return () => {
      isMounted = false
    }
  }, [])

  // 2. Tải GeoJSON khi thay đổi cấp hành chính (tỉnh <-> phường)
  useEffect(() => {
    let isMounted = true

    fetchRegions(level, 0.001)
      .then((data) => {
        if (!isMounted) return
        setGeoJsonState({ level, data })
        setGeoJsonError(null)
        setLoadingGeoJson(false)
      })
      .catch((err) => {
        if (!isMounted) return
        console.error('Lỗi tải GeoJSON:', err)
        setGeoJsonError(`Lỗi tải ranh giới ${level}: ${err.message}`)
        setLoadingGeoJson(false)
      })

    return () => {
      isMounted = false
    }
  }, [level])

  // 3. Tải giá trị KPI khi bộ lọc thay đổi
  useEffect(() => {
    if (!selectedKpi || !at || !selectedSource) return

    let isMounted = true

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
        setKpiError(null)
        setLoadingKpi(false)
      })
      .catch((err) => {
        if (!isMounted) return
        console.error('Lỗi tải KPI values:', err)
        setKpiError(`Lỗi tải số liệu KPI: ${err.message}`)
        setLoadingKpi(false)
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

  // Duyệt toàn bộ danh sách items để lấy mốc updated_at mới nhất khác null
  const latestUpdatedAt = useMemo(() => {
    const items = kpiResponse?.items
    if (!items?.length) return null

    let latest = null
    let latestMs = -Infinity
    for (const item of items) {
      if (!item?.updated_at) continue
      const ms = Date.parse(item.updated_at)
      if (!Number.isNaN(ms)) {
        if (ms > latestMs) {
          latestMs = ms
          latest = item.updated_at
        }
      } else if (latest === null || item.updated_at > latest) {
        latest = item.updated_at
      }
    }
    return latest
  }, [kpiResponse])

  // Nguồn dữ liệu hiện tại
  const currentSourceMeta = useMemo(() => {
    return sources.find((s) => s.source_code === selectedSource) || kpiResponse?.source
  }, [sources, selectedSource, kpiResponse])

  // Handlers cập nhật bộ lọc kèm trạng thái loading/lỗi tương ứng
  const handleChangeLevel = (newLevel) => {
    if (newLevel === level) return
    setLevel(newLevel)
    setLoadingGeoJson(true)
    setGeoJsonError(null)
    setLoadingKpi(true)
    setKpiError(null)
  }

  const handleSelectKpi = (newKpi) => {
    setSelectedKpi(newKpi)
    setLoadingKpi(true)
    setKpiError(null)
  }

  const handleChangePeriodType = (newType) => {
    setPeriodType(newType)
    setLoadingKpi(true)
    setKpiError(null)
    if (newType === 'day' && at.includes('T')) {
      setAt(at.substring(0, 10))
    } else if (newType === 'hour' && !at.includes('T')) {
      setAt(`${at}T10:00`)
    }
  }

  const handleChangeAt = (newAt) => {
    setAt(newAt)
    setLoadingKpi(true)
    setKpiError(null)
  }

  const handleChangeSource = (newSource) => {
    setSelectedSource(newSource)
    setLoadingKpi(true)
    setKpiError(null)
  }

  const handleDismissErrors = () => {
    setInitError(null)
    setGeoJsonError(null)
    setKpiError(null)
  }

  return (
    <div className="app-container">
      {/* Thanh công cụ lọc */}
      <FilterBar
        kpis={kpis}
        selectedKpi={selectedKpi}
        onSelectKpi={handleSelectKpi}
        level={level}
        onChangeLevel={handleChangeLevel}
        periodType={periodType}
        onChangePeriodType={handleChangePeriodType}
        at={at}
        onChangeAt={handleChangeAt}
        sources={sources}
        selectedSource={selectedSource}
        onChangeSource={handleChangeSource}
        loading={isLoading}
      />

      {/* Thông báo lỗi gộp nếu có (không ghi đè lẫn nhau) */}
      {errorMessages.length > 0 && (
        <div className="error-banner">
          <div className="error-list">
            {errorMessages.map((msg, idx) => (
              <div key={idx}>⚠️ {msg}</div>
            ))}
          </div>
          <button className="error-close-btn" onClick={handleDismissErrors}>
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
          onDrillDownWard={() => handleChangeLevel('ward')}
          onBackToProvince={() => handleChangeLevel('province')}
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
