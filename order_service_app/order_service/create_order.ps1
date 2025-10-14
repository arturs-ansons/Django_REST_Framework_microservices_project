# ===============================
# create_order.ps1
# ===============================

# -------------------------------
# Configuration
# -------------------------------
$userServiceUrl = "http://localhost:8000/api/users/"
$orderServiceUrl = "http://localhost:8003/api/orders/"
$username = "rambo4"   # Change to your test user
$password = "12345678"  # Change to your test user's password
$productId = 1
$quantity = 2

# -------------------------------
# 1️⃣ Get JWT token from user_service
# -------------------------------
$loginUrl = "http://localhost:8000/api/token/"  # Default SimpleJWT endpoint
$loginBody = @{
    username = $username
    password = $password
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri $loginUrl -Method POST -Body $loginBody -ContentType "application/json"
    $token = $loginResponse.access
    Write-Host "Access token:`n$token`n"
} catch {
    Write-Error "Failed to login: $($_.Exception.Message)"
    exit
}

# -------------------------------
# 2️⃣ Create order in order_service
# -------------------------------
$orderBody = @{
    product_id = $productId
    quantity   = $quantity
} | ConvertTo-Json

try {
    $orderResponse = Invoke-RestMethod -Uri $orderServiceUrl -Method POST -Body $orderBody -ContentType "application/json" -Headers @{ Authorization = "Bearer $token" }
    Write-Host "Order created successfully:`n$($orderResponse | ConvertTo-Json -Depth 5)"
} catch {
    # Safely read response content if available
    $errorContent = if ($_.Exception.Response) { $_.Exception.Response.GetResponseStream() | % { (New-Object IO.StreamReader($_)).ReadToEnd() } } else { $_.Exception.Message }
    Write-Error "Failed to create order: $errorContent"
}
