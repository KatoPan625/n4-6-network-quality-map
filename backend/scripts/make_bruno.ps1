# Sinh Bruno collection trong thu muc bruno/ (chay lai de cap nhat)
# Ghi UTF-8 KHONG BOM vi Bruno khong doc duoc BOM
function Save($path, $text) { [IO.File]::WriteAllText($path, $text, (New-Object Text.UTF8Encoding $false)) }

$root = Join-Path $PSScriptRoot "..\bruno"
New-Item -ItemType Directory -Force "$root\environments" | Out-Null
Save "$root\bruno.json" '{ "version": "1", "name": "N4.6 Backend API", "type": "collection" }'
Save "$root\environments\local.bru" "vars {`n  baseUrl: http://localhost:8000`n}`n"

$reqs = @(
  @("01 Health DB",       "/health/db",   200, 'expect(res.getBody().status).to.equal("ok");'),
  @("02 KPI list",        "/api/v1/kpis", 200, 'expect(res.getBody().length).to.equal(4);'),
  @("03 Sources",         "/api/v1/sources", 200, 'expect(res.getBody()[0].is_default).to.equal(true);'),
  @("04 Regions tinh",    "/api/v1/regions", 200, 'expect(res.getBody().features.length).to.equal(34);'),
  @("05 Regions phuong",  "/api/v1/regions?level=ward", 200, 'expect(res.getBody().features.length).to.equal(168);'),
  @("06 KPI values gio",  "/api/v1/kpi-values?kpi=cssr&level=ward&at=2026-10-02T20:00&source=BE-SAMPLE", 200, 'expect(res.getBody().items.length).to.equal(168); expect(res.getBody().source.data_nature).to.equal("simulated");'),
  @("07 KPI values ngay", "/api/v1/kpi-values?kpi=traffic&period_type=day&at=2026-10-02&source=BE-SAMPLE", 200, 'expect(res.getBody().items.length).to.equal(34);'),
  @("08 Region detail",   "/api/v1/regions/25760/kpis?source=BE-SAMPLE", 200, 'expect(res.getBody().kpis.length).to.equal(4);'),
  @("09 Compare",         "/api/v1/compare?kpi=cssr&a=2026-10-01&b=2026-10-02&source=BE-SAMPLE", 200, 'expect(res.getBody().items.length).to.equal(34);'),
  @("10 Unknown KPI 404", "/api/v1/kpi-values?kpi=khong_co&at=2026-10-02T20:00&source=BE-SAMPLE", 404, ''),
  @("11 Gio le 422",      "/api/v1/kpi-values?kpi=cssr&at=2026-10-02T20:30&source=BE-SAMPLE", 422, '')
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
