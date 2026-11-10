# Sinh Bruno collection trong thu muc bruno/ (chay lai de cap nhat)
# Ghi UTF-8 KHONG BOM vi Bruno khong doc duoc BOM
function Save($path, $text) { [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false)) }

$root = Join-Path $PSScriptRoot "..\bruno"
New-Item -ItemType Directory -Force "$root\environments" | Out-Null
Save "$root\bruno.json" '{ "version": "1", "name": "N4.6 Backend API", "type": "collection" }'
Save "$root\environments\local.bru" "vars {`n  baseUrl: http://localhost:8000`n}`n"

$reqs = @(
  @("01 Health DB",       "/health/db",   200, 'expect(res.getBody().status).to.equal("ok");'),
  @("02 KPI list",        "/api/v1/kpis", 200, 'expect(res.getBody().length).to.be.above(0);'),
  @("03 Regions GeoJSON", "/api/v1/regions", 200, 'expect(res.getBody().type).to.equal("FeatureCollection");'),
  @("04 KPI values",      "/api/v1/kpi-values?kpi=latency_ms&period_start=2026-10-01", 200, 'expect(res.getBody().items.length).to.equal(9);'),
  @("05 Region detail",   "/api/v1/regions/R-1-1/kpis", 200, 'expect(res.getBody().kpis.length).to.be.above(0);'),
  @("06 Compare",         "/api/v1/compare?kpi=latency_ms&period_a=2026-09-01&period_b=2026-10-01", 200, 'expect(res.getBody().items.length).to.equal(9);'),
  @("07 Unknown KPI 404", "/api/v1/kpi-values?kpi=khong_co&period_start=2026-10-01", 404, ''),
  @("08 Bad date 422",    "/api/v1/kpi-values?kpi=latency_ms&period_start=10-2026", 422, '')
)
$i = 0
foreach ($r in $reqs) {
  $i++
  $extra = if ($r[3]) { "`n    $($r[3])" } else { "" }
  $body = "meta {`n  name: $($r[0])`n  type: http`n  seq: $i`n}`n`n" +
          "get {`n  url: {{baseUrl}}$($r[1])`n  body: none`n  auth: none`n}`n`n" +
          "tests {`n  test(""status $($r[2])"", function() {`n    expect(res.getStatus()).to.equal($($r[2]));$extra`n  });`n}`n"
  Save (Join-Path $root "$($r[0]).bru") $body
}
Write-Output "Da tao $i request trong $root"
