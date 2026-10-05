param([switch]$Help, [string]$BaseUrl = "http://localhost:8080")

[Console]::InputEncoding = [System.Text.UTF8Encoding]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$OutputEncoding = [System.Text.UTF8Encoding]::new()

function Write-Title([string]$Text) {
  Write-Host "`n=== $Text ===" -ForegroundColor Cyan
}

function Write-ApiError($Response) {
  $detail = if ($Response.Data -and $Response.Data.detail) { $Response.Data.detail } else { $Response.Raw }
  Write-Host "Erro na chamada da API: $detail" -ForegroundColor Red
}

function Invoke-Api([string]$Method, [string]$Path, $Body) {
  $arguments = @("--silent", "--show-error", "--fail-with-body", "-X", $Method, "$BaseUrl$Path")
  if ($Body) {
    $json = ($Body | ConvertTo-Json -Compress).Replace('"', '\"')
    $arguments += @("-H", "Content-Type: application/json", "--data-raw", $json)
  }
  $raw = (& curl.exe @arguments 2>$null | Out-String).Trim()
  try { $data = $raw | ConvertFrom-Json } catch { $data = $null }
  return [PSCustomObject]@{ Success = ($LASTEXITCODE -eq 0); Data = $data; Raw = $raw }
}

function Write-Metrics($Model) {
  $metrics = $Model.metrics
  [PSCustomObject]@{
    Modelo = $Model.model
    Versão = $Model.version
    Cutoff = $Model.model_cutoff
    'MAE' = if ($null -ne $metrics.mae) { '{0:N4}' -f $metrics.mae } else { 'não informado' }
    'Acurácia direcional' = if ($null -ne $metrics.direction_accuracy) { '{0:P2}' -f $metrics.direction_accuracy } else { 'não informada' }
    'Recall de alta' = if ($null -ne $metrics.direction_recall_up) { '{0:P2}' -f $metrics.direction_recall_up } else { 'não aplicável' }
  }
}

function Show-Status {
  $response = Invoke-Api "GET" "/v1/status" $null
  if (!$response.Success) { Write-ApiError $response; return }
  Write-Title "Status da plataforma"
  $response.Data.models | ForEach-Object { Write-Metrics $_ } | Format-Table -AutoSize
  Write-Host "Janelas disponíveis para inferência: $($response.Data.datasets.inference -join ', ')"
  Write-Host "Lotes disponíveis para retreino:    $($response.Data.datasets.retraining -join ', ')"
}

function Show-Results {
  $response = Invoke-Api "GET" "/v1/models/results" $null
  if (!$response.Success) { Write-ApiError $response; return }
  Write-Title "Métricas dos modelos"
  $response.Data.models | ForEach-Object { Write-Metrics $_ } | Format-Table -AutoSize
  foreach ($model in $response.Data.models) {
    Write-Host "$($model.model): $($model.evaluation)"
  }
}

function Show-Predictions {
  $response = Invoke-Api "GET" "/v1/predictions" $null
  if (!$response.Success) { Write-ApiError $response; return }
  Write-Title "Predições passadas"
  foreach ($model in $response.Data.models) {
    Write-Host "`nModelo: $($model.model)" -ForegroundColor Yellow
    if ($model.predictions) {
      $model.predictions | Select-Object cutoff, target_date, actual, prophet_yhat | Format-Table -AutoSize
    } else {
      Write-Host $model.note
    }
  }
}

function Show-Inference($Dataset) {
  $response = Invoke-Api "POST" "/v1/inferences" @{ dataset = $Dataset }
  if (!$response.Success) { Write-ApiError $response; return }
  Write-Title "Inferência para $($response.Data.dataset)"
  foreach ($model in $response.Data.models) {
    Write-Host "`n$($model.model.ToUpper()) — $($model.version)" -ForegroundColor Yellow
    Write-Host "Último fechamento conhecido: R$ $($model.last_close.ToString('N4'))"
    Write-Host "Fechamento estimado (5 dias úteis): R$ $($model.forecast_close.ToString('N4'))"
    $direction = $model.direction.ToUpper()
    $color = if ($direction -eq 'ALTA') { 'Green' } elseif ($direction -eq 'QUEDA') { 'Red' } else { 'Yellow' }
    Write-Host "Direção estimada: $direction" -ForegroundColor $color
    Write-Metrics $model | Format-List
  }
  Write-Host $response.Data.disclaimer -ForegroundColor DarkYellow
}

function Select-Dataset([string]$Kind) {
  $response = Invoke-Api "GET" "/v1/datasets?kind=$Kind" $null
  if (!$response.Success) { Write-ApiError $response; return $null }
  $items = @($response.Data.datasets)
  if ($items.Count -eq 0) { Write-Host "Nenhum CSV disponível para $Kind."; return $null }
  for ($i = 0; $i -lt $items.Count; $i++) { Write-Host "[$($i + 1)] $($items[$i])" }
  $chosenText = Read-Host "Selecione o CSV"
  if ($chosenText -notmatch '^\d+$') { Write-Host "Seleção inválida." -ForegroundColor Red; return $null }
  $chosen = [int]$chosenText - 1
  if ($chosen -lt 0 -or $chosen -ge $items.Count) { Write-Host "Seleção inválida." -ForegroundColor Red; return $null }
  return $items[$chosen]
}

function Request-Retraining($Dataset) {
  $response = Invoke-Api "POST" "/v1/retraining-requests" @{ dataset = $Dataset }
  if (!$response.Success) { Write-ApiError $response; return }
  Write-Title "Retreino solicitado"
  Write-Host "Lote: $($response.Data.dataset)"
  Write-Host "Identificador: $($response.Data.id)"
  Write-Host "Situação inicial: $($response.Data.status)"
  Start-Sleep -Seconds 3
  $status = Invoke-Api "GET" "/v1/retraining-requests/$($response.Data.id)" $null
  if (!$status.Success) { Write-ApiError $status; return }
  Write-Host "Situação final: $($status.Data.status)"
  if ($status.Data.details.rows) { Write-Host "Linhas validadas: $($status.Data.details.rows)" }
  if ($status.Data.details.candidates) {
    Write-Host "`nResultado da simulação" -ForegroundColor Yellow
    foreach ($model in @('prophet', 'sarima')) {
      $candidate = $status.Data.details.candidates.$model
      $champion = $status.Data.details.champions.$model
      Write-Host "`n$($model.ToUpper()) candidato treinado" -ForegroundColor Yellow
      Write-Host "Acurácia direcional: $([string]::Format('{0:P2}', $candidate.direction_accuracy)) | campeão $($champion.version): $([string]::Format('{0:P2}', $champion.direction_accuracy))"
      Write-Host "MAE: $([string]::Format('{0:N4}', $candidate.mae)) | campeão: $([string]::Format('{0:N4}', $champion.mae))"
      Write-Host "Comparação: $($status.Data.details.comparison.$model)" -ForegroundColor DarkYellow
    }
    Write-Host "Decisão: NÃO PROMOVIDO — os artefatos atuais foram preservados." -ForegroundColor Red
    Write-Host $status.Data.details.reason -ForegroundColor DarkYellow
  }
  if ($status.Data.details.error) { Write-Host "Motivo: $($status.Data.details.error)" -ForegroundColor Red }
}

if ($Help) {
  Write-Host "Uso: .\client\terminal.ps1"
  Write-Host "O menu consulta status, métricas, predições passadas, inferência e retreino."
  Write-Host "Todas as requisições são enviadas com curl.exe para $BaseUrl."
  exit 0
}

do {
  Write-Host "`n[1] Status  [2] Resultados  [3] Predições passadas  [4] Nova inferência  [5] Retreino  [0] Sair" -ForegroundColor White
  $option = Read-Host "Opção"
  if ($null -eq $option) { break }
  $option = $option.Trim()
  switch ($option) {
    "1" { Show-Status }
    "2" { Show-Results }
    "3" { Show-Predictions }
    "4" { $dataset = Select-Dataset "inference"; if ($dataset) { Show-Inference $dataset } }
    "5" { $dataset = Select-Dataset "retraining"; if ($dataset) { Request-Retraining $dataset } }
    "0" { Write-Host "Até logo." }
    default { Write-Host "Opção inválida." -ForegroundColor Red }
  }
} while ($option -ne "0")
