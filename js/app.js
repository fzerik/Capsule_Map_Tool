// 全局变量
// 默认使用同源 API；部署到独立后端时可在页面加载前设置 window.CAPSULE_API_BASE_URL。
const API_BASE_URL = (window.CAPSULE_API_BASE_URL || '/api').replace(/\/$/, '');
const API_KEY_STORAGE = {
    google: 'capsule-map-google-api-key',
    amap: 'capsule-map-amap-api-key'
};
let map = null;
let batchMap = null;
let batchResults = [];
let batchProvider = 'google';

function getApiKey(provider) {
    const inputId = provider === 'amap' ? 'amap-api-key' : 'google-api-key';
    const input = document.getElementById(inputId);
    return input ? input.value.trim() : '';
}

function loadApiKeys() {
    Object.entries(API_KEY_STORAGE).forEach(([provider, storageKey]) => {
        const inputId = provider === 'amap' ? 'amap-api-key' : 'google-api-key';
        const input = document.getElementById(inputId);
        if (!input) return;
        try {
            input.value = localStorage.getItem(storageKey) || '';
        } catch (error) {
            console.warn('无法读取浏览器本地 API Key:', error);
        }

        input.addEventListener('input', () => {
            try {
                localStorage.setItem(storageKey, input.value);
            } catch (error) {
                console.warn('无法保存浏览器本地 API Key:', error);
            }
        });
    });
}

function clearApiKeys() {
    Object.values(API_KEY_STORAGE).forEach(storageKey => {
        try {
            localStorage.removeItem(storageKey);
        } catch (error) {
            console.warn('无法清除浏览器本地 API Key:', error);
        }
    });
    ['google-api-key', 'amap-api-key'].forEach(inputId => {
        const input = document.getElementById(inputId);
        if (input) input.value = '';
    });
    showNotification('已清除浏览器本地保存的 API Key', 'success');
}

function updateProviderNotice(selectId, noticeId) {
    const providerSelect = document.getElementById(selectId);
    const notice = document.getElementById(noticeId);
    if (!providerSelect || !notice) return;

    const provider = providerSelect.value;
    if (provider === 'amap') {
        notice.className = 'provider-notice warning-notice';
        notice.textContent = '高德返回 GCJ-02 坐标，与 WGS84 存在偏移；本功能不显示高德结果地图，叠加其他底图前请先转换坐标系。';
    } else {
        notice.className = 'provider-notice info-notice';
        notice.textContent = 'Google Maps 返回 WGS84 坐标，本页面支持显示地图。';
    }
}

function updateSingleMapVisibility(provider) {
    const mapContainer = document.getElementById('map-container');
    if (!mapContainer) return;
    mapContainer.classList.toggle('hidden', provider === 'amap');
}

function updateBatchMapVisibility(provider) {
    const showMapBtn = document.getElementById('show-map-btn');
    const batchMapContainer = document.getElementById('batch-map-container');
    if (!showMapBtn || !batchMapContainer) return;

    const canShowMap = provider === 'google';
    showMapBtn.classList.toggle('hidden', !canShowMap);
    if (!canShowMap) {
        batchMapContainer.classList.add('hidden');
        showMapBtn.textContent = '显示地图';
        if (batchMap) {
            batchMap.remove();
            batchMap = null;
        }
    }
}

// DOM元素
document.addEventListener('DOMContentLoaded', () => {
    loadApiKeys();

    const clearApiKeysButton = document.getElementById('clear-api-keys');
    if (clearApiKeysButton) {
        clearApiKeysButton.addEventListener('click', clearApiKeys);
    }

    const geocodeProvider = document.getElementById('geocode-provider');
    const batchGeocodeProvider = document.getElementById('batch-geocode-provider');
    if (geocodeProvider) {
        geocodeProvider.addEventListener('change', () => {
            updateProviderNotice('geocode-provider', 'geocode-provider-notice');
            updateSingleMapVisibility(geocodeProvider.value);
        });
        updateProviderNotice('geocode-provider', 'geocode-provider-notice');
        updateSingleMapVisibility(geocodeProvider.value);
    }
    if (batchGeocodeProvider) {
        batchGeocodeProvider.addEventListener('change', () => {
            updateProviderNotice('batch-geocode-provider', 'batch-geocode-provider-notice');
            updateBatchMapVisibility(batchGeocodeProvider.value);
        });
        updateProviderNotice('batch-geocode-provider', 'batch-geocode-provider-notice');
        updateBatchMapVisibility(batchGeocodeProvider.value);
    }

    // 地址模块的子菜单切换。坐标和地图模块分别由各自脚本处理，避免全局状态互相清除。
    const tabBtns = document.querySelectorAll('#geocode-tab .tab-btn');
    const tabPanes = document.querySelectorAll('#geocode-tab .tab-pane');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            tabPanes.forEach(pane => {
                pane.classList.remove('active');
                if (pane.id === `${tabId}-tab`) {
                    pane.classList.add('active');
                }
            });
        });
    });
    
    // 单个地址转换
    const geocodeBtn = document.getElementById('geocode-btn');
    const addressInput = document.getElementById('address');
    
    geocodeBtn.addEventListener('click', () => {
        const address = addressInput.value.trim();
        if (!address) {
            showNotification('请输入地址', 'error');
            return;
        }
        geocodeAddress(address);
    });
    
    addressInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') geocodeBtn.click();
    });
    
    // 批量地址转换
    const batchGeocodeBtn = document.getElementById('batch-geocode-btn');
    const fileUpload = document.getElementById('file-upload');
    
    batchGeocodeBtn.addEventListener('click', () => {
        const file = fileUpload.files[0];
        if (!file) {
            showNotification('请选择文件', 'error');
            return;
        }
        batchGeocodeAddresses(file);
    });
    
    document.getElementById('download-csv').addEventListener('click', downloadResultsAsCSV);
    
    // 只有 Google 结果允许显示地图
    const showMapBtn = document.getElementById('show-map-btn');
    showMapBtn.addEventListener('click', () => {
        const batchMapContainer = document.getElementById('batch-map-container');
        batchMapContainer.classList.toggle('hidden');
        
        if (!batchMapContainer.classList.contains('hidden')) {
            showMapBtn.textContent = '隐藏地图';
            if (!batchMap) initBatchMap();
            setTimeout(() => {
                if (batchMap) batchMap.invalidateSize();
            }, 100);
        } else {
            showMapBtn.textContent = '显示地图';
        }
    });
});

// 单个地址转换为经纬度
async function geocodeAddress(address) {
    try {
        const geocodeBtn = document.getElementById('geocode-btn');
        const originalBtnText = geocodeBtn.textContent;
        geocodeBtn.textContent = '处理中...';
        geocodeBtn.disabled = true;
        
        const provider = document.getElementById('geocode-provider').value;
        const response = await fetch(`${API_BASE_URL}/geocode`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                address,
                provider,
                api_key: getApiKey(provider)
            })
        });
        const data = await response.json();
        
        geocodeBtn.textContent = originalBtnText;
        geocodeBtn.disabled = false;
        
        if (data.status === 'success') {
            displaySingleResult(address, data);
        } else {
            showNotification(data.message || '地理编码失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('请求失败，请检查网络连接或服务器状态', 'error');
        const geocodeBtn = document.getElementById('geocode-btn');
        geocodeBtn.textContent = '转换';
        geocodeBtn.disabled = false;
    }
}

// 显示单个地址转换结果；高德结果不显示地图，避免 GCJ02/WGS84 偏移。
function displaySingleResult(originalAddress, data) {
    const setText = (id, value) => {
        const element = document.getElementById(id);
        if (element) element.textContent = value;
    };

    setText('original-address', originalAddress);
    setText('formatted-address', data.formatted_address);
    setText('latitude', data.latitude);
    setText('longitude', data.longitude);
    setText('coordinate-system', data.coordinate_system || '未知');

    const resultCard = document.getElementById('result-card');
    if (resultCard) resultCard.classList.remove('hidden');

    const mapContainer = document.getElementById('map-container');
    const isGoogleResult = data.provider === 'google' || !data.provider;
    if (!mapContainer) return;
    mapContainer.classList.toggle('hidden', !isGoogleResult);

    if (!isGoogleResult) {
        if (map) map.invalidateSize();
        return;
    }

    if (!map) {
        map = L.map('map-container').setView([data.latitude, data.longitude], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
    } else {
        map.setView([data.latitude, data.longitude], 13);
        map.invalidateSize();
    }

    map.eachLayer(layer => {
        if (layer instanceof L.Marker) map.removeLayer(layer);
    });

    L.marker([data.latitude, data.longitude])
        .addTo(map)
        .bindPopup(data.formatted_address)
        .openPopup();
}

// 批量地址转换
async function batchGeocodeAddresses(file) {
    try {
        document.getElementById('progress-container').classList.remove('hidden');
        document.getElementById('batch-results').classList.add('hidden');
        document.getElementById('batch-map-container').classList.add('hidden');
        
        const batchGeocodeBtn = document.getElementById('batch-geocode-btn');
        const originalBtnText = batchGeocodeBtn.textContent;
        batchGeocodeBtn.textContent = '处理中...';
        batchGeocodeBtn.disabled = true;
        
        const provider = document.getElementById('batch-geocode-provider').value;
        batchProvider = provider;
        updateBatchMapVisibility(provider);

        const formData = new FormData();
        formData.append('file', file);
        formData.append('provider', provider);
        formData.append('api_key', getApiKey(provider));
        
        const response = await fetch(`${API_BASE_URL}/batch-geocode`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        
        batchGeocodeBtn.textContent = originalBtnText;
        batchGeocodeBtn.disabled = false;
        document.getElementById('progress-container').classList.add('hidden');
        
        if (data.status === 'success') {
            batchResults = data.results;
            batchProvider = data.provider || provider;
            updateBatchMapVisibility(batchProvider);
            displayBatchResults(data.results);
        } else {
            showNotification(data.message || '批量地理编码失败', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        showNotification('请求失败，请检查网络连接或服务器状态', 'error');
        const batchGeocodeBtn = document.getElementById('batch-geocode-btn');
        batchGeocodeBtn.textContent = '批量转换';
        batchGeocodeBtn.disabled = false;
        document.getElementById('progress-container').classList.add('hidden');
    }
}

// 显示批量转换结果
function displayBatchResults(results) {
    const tableBody = document.getElementById('results-body');
    tableBody.innerHTML = '';
    
    results.forEach(result => {
        const row = document.createElement('tr');
        if (result.status === 'error') row.style.backgroundColor = 'rgba(234, 67, 53, 0.1)';
        
        const values = [
            result.original_address,
            result.status === 'success' ? result.formatted_address : '-',
            result.status === 'success' ? result.latitude : '-',
            result.status === 'success' ? result.longitude : '-',
            result.status === 'success' ? result.coordinate_system : '-',
            result.status === 'success' ? '成功' : '失败'
        ];
        values.forEach((value, index) => {
            const cell = document.createElement('td');
            cell.textContent = value;
            if (index === values.length - 1) {
                cell.style.color = result.status === 'success' ? 'var(--success-color)' : 'var(--error-color)';
            }
            row.appendChild(cell);
        });
        tableBody.appendChild(row);
    });
    
    document.getElementById('batch-results').classList.remove('hidden');
}

// 初始化批量地图（仅 Google/WGS84 结果允许调用）
function initBatchMap() {
    if (batchProvider !== 'google') return;

    batchMap = L.map('batch-map-container').setView([0, 0], 2);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(batchMap);
    
    const validResults = batchResults.filter(result => result.status === 'success');
    if (validResults.length === 0) {
        showNotification('没有有效的地理编码结果可以在地图上显示', 'warning');
        return;
    }
    
    const bounds = L.latLngBounds();
    validResults.forEach(result => {
        L.marker([result.latitude, result.longitude])
            .addTo(batchMap)
            .bindPopup(result.formatted_address);
        bounds.extend([result.latitude, result.longitude]);
    });
    
    batchMap.fitBounds(bounds, { padding: [50, 50] });
}

// 下载结果为CSV
function downloadResultsAsCSV() {
    if (batchResults.length === 0) {
        showNotification('没有可下载的结果', 'warning');
        return;
    }

    const escapeCsv = value => `"${String(value ?? '').replace(/"/g, '""')}"`;
    let csvContent = '\ufeff原始地址,格式化地址,纬度,经度,坐标系,状态\n';

    batchResults.forEach(result => {
        const formattedAddress = result.status === 'success' ? result.formatted_address : '';
        const latitude = result.status === 'success' ? result.latitude : '';
        const longitude = result.status === 'success' ? result.longitude : '';
        const coordinateSystem = result.status === 'success' ? result.coordinate_system : '';
        const status = result.status === 'success' ? '成功' : (result.message || '失败');

        csvContent += [
            result.original_address,
            formattedAddress,
            latitude,
            longitude,
            coordinateSystem,
            status
        ].map(escapeCsv).join(',') + '\n';
    });

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = '地址转经纬度结果.csv';
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// 显示通知
function showNotification(message, type = 'info') {
    // 创建通知元素
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // 添加到页面
    document.body.appendChild(notification);
    
    // 显示通知
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // 自动关闭
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
} 