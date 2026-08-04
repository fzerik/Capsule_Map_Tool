/**
 * 坐标转换功能的JavaScript代码
 */
// API_BASE_URL 由 app.js 全局定义，这里直接使用

document.addEventListener('DOMContentLoaded', function() {
    const mainTabBtns = document.querySelectorAll('.main-tab-btn');
    const mainTabPanes = document.querySelectorAll('.main-tab-pane');

    // 进入主菜单时，自动展开该菜单的第一个子菜单。
    function activateDefaultSubTab(mainTabPane) {
        const childTabBtns = mainTabPane.querySelectorAll('.tabs .tab-btn');
        const childTabPanes = mainTabPane.querySelectorAll('.tab-content .tab-pane');

        if (childTabBtns.length === 0 || childTabPanes.length === 0) return;

        childTabBtns.forEach(tabBtn => tabBtn.classList.remove('active'));
        childTabPanes.forEach(tabPane => tabPane.classList.remove('active'));
        childTabBtns[0].classList.add('active');
        childTabPanes[0].classList.add('active');
    }

    mainTabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const mainTabId = this.getAttribute('data-main-tab');
            const targetPane = document.getElementById(`${mainTabId}-tab`);
            if (!targetPane) return;
            
            // 移除所有主菜单的 active 状态
            mainTabBtns.forEach(tabBtn => tabBtn.classList.remove('active'));
            mainTabPanes.forEach(pane => pane.classList.remove('active'));
            
            // 激活当前主菜单，并展开其第一个子菜单
            this.classList.add('active');
            targetPane.classList.add('active');
            activateDefaultSubTab(targetPane);
        });
    });

    // 坐标转换标签页切换
    const coordTabBtns = document.querySelectorAll('#coordinate-tab .tab-btn');
    const coordTabPanes = document.querySelectorAll('#coordinate-tab .tab-pane');

    coordTabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有标签页的active类
            coordTabBtns.forEach(btn => btn.classList.remove('active'));
            coordTabPanes.forEach(pane => pane.classList.remove('active'));
            
            // 添加当前标签页的active类
            this.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // 单个坐标转换
    const convertCoordBtn = document.getElementById('convert-coord-btn');
    const sourceCoordSystem = document.getElementById('source-coord-system');
    const targetCoordSystem = document.getElementById('target-coord-system');
    const longitudeInput = document.getElementById('longitude-input');
    const latitudeInput = document.getElementById('latitude-input');
    const coordResultCard = document.getElementById('coord-result-card');

    // 单个坐标转换按钮点击事件
    convertCoordBtn.addEventListener('click', function() {
        const sourceSys = sourceCoordSystem.value;
        const targetSys = targetCoordSystem.value;
        const lng = parseFloat(longitudeInput.value);
        const lat = parseFloat(latitudeInput.value);

        if (isNaN(lng) || isNaN(lat)) {
            showNotification('请输入有效的经纬度坐标', 'error');
            return;
        }

        // 显示加载状态
        convertCoordBtn.disabled = true;
        convertCoordBtn.textContent = '转换中...';

        // 调用API进行坐标转换
        fetch(`${API_BASE_URL}/convert-coordinate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                source_system: sourceSys,
                target_system: targetSys,
                longitude: lng,
                latitude: lat
            })
        })
        .then(response => response.json())
        .then(data => {
            convertCoordBtn.disabled = false;
            convertCoordBtn.textContent = '转换';

            if (data.status === 'success') {
                // 显示结果
                document.getElementById('source-system').textContent = getCoordSystemName(sourceSys);
                document.getElementById('target-system').textContent = getCoordSystemName(targetSys);
                document.getElementById('source-longitude').textContent = lng.toFixed(6);
                document.getElementById('source-latitude').textContent = lat.toFixed(6);
                document.getElementById('target-longitude').textContent = data.result.longitude.toFixed(6);
                document.getElementById('target-latitude').textContent = data.result.latitude.toFixed(6);
                
                coordResultCard.classList.remove('hidden');
                showNotification('坐标转换成功', 'success');
            } else {
                showNotification(data.message || '坐标转换失败', 'error');
            }
        })
        .catch(error => {
            convertCoordBtn.disabled = false;
            convertCoordBtn.textContent = '转换';
            showNotification('请求失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });

    // 批量坐标转换
    const batchConvertCoordBtn = document.getElementById('batch-convert-coord-btn');
    const batchSourceCoordSystem = document.getElementById('batch-source-coord-system');
    const batchTargetCoordSystem = document.getElementById('batch-target-coord-system');
    const coordFileUpload = document.getElementById('coord-file-upload');
    const coordProgressContainer = document.getElementById('coord-progress-container');
    const batchCoordResultsContainer = document.getElementById('batch-coord-results');
    const coordResultsBody = document.getElementById('coord-results-body');
    const downloadCoordCsvBtn = document.getElementById('download-coord-csv');

    // 批量坐标转换按钮点击事件
    batchConvertCoordBtn.addEventListener('click', function() {
        const file = coordFileUpload.files[0];
        if (!file) {
            showNotification('请选择文件', 'error');
            return;
        }

        const sourceSys = batchSourceCoordSystem.value;
        const targetSys = batchTargetCoordSystem.value;

        // 显示进度条
        coordProgressContainer.classList.remove('hidden');
        batchCoordResultsContainer.classList.add('hidden');
        batchConvertCoordBtn.disabled = true;

        const formData = new FormData();
        formData.append('file', file);
        formData.append('source_system', sourceSys);
        formData.append('target_system', targetSys);

        // 调用API进行批量坐标转换
        fetch(`${API_BASE_URL}/batch-convert-coordinate`, {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            batchConvertCoordBtn.disabled = false;
            coordProgressContainer.classList.add('hidden');

            if (data.status === 'success') {
                // 保存结果数据
                const results = data.results;
                
                // 清空表格
                coordResultsBody.innerHTML = '';
                
                // 填充表格
                data.results.forEach(result => {
                    const row = document.createElement('tr');
                    
                    const sourceLngCell = document.createElement('td');
                    sourceLngCell.textContent = result.source_longitude.toFixed(6);
                    row.appendChild(sourceLngCell);
                    
                    const sourceLatCell = document.createElement('td');
                    sourceLatCell.textContent = result.source_latitude.toFixed(6);
                    row.appendChild(sourceLatCell);
                    
                    const targetLngCell = document.createElement('td');
                    targetLngCell.textContent = result.target_longitude.toFixed(6);
                    row.appendChild(targetLngCell);
                    
                    const targetLatCell = document.createElement('td');
                    targetLatCell.textContent = result.target_latitude.toFixed(6);
                    row.appendChild(targetLatCell);
                    
                    const statusCell = document.createElement('td');
                    statusCell.textContent = result.status === 'success' ? '成功' : '失败';
                    statusCell.className = result.status === 'success' ? 'success-status' : 'error-status';
                    row.appendChild(statusCell);
                    
                    coordResultsBody.appendChild(row);
                });
                
                // 显示结果
                batchCoordResultsContainer.classList.remove('hidden');
                showNotification(`成功转换 ${data.results.length} 个坐标`, 'success');
            } else {
                showNotification(data.message || '批量坐标转换失败', 'error');
            }
        })
        .catch(error => {
            batchConvertCoordBtn.disabled = false;
            coordProgressContainer.classList.add('hidden');
            showNotification('请求失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });

    // 下载CSV按钮点击事件
    downloadCoordCsvBtn.addEventListener('click', function() {
        const results = document.querySelectorAll('#coord-results-body tr');
        if (results.length === 0) {
            showNotification('没有可下载的数据', 'warning');
            return;
        }

        // 创建CSV内容
        let csvContent = '源经度,源纬度,转换后经度,转换后纬度,状态\n';
        
        results.forEach(row => {
            const cells = row.querySelectorAll('td');
            const rowData = Array.from(cells).map(cell => cell.textContent);
            csvContent += rowData.join(',') + '\n';
        });
        
        // 创建Blob对象
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `坐标转换结果_${new Date().toISOString().slice(0, 10)}.csv`);
        document.body.appendChild(link);
        
        // 触发下载
        link.click();
        
        // 清理
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    });

    // 辅助函数：获取坐标系统名称
    function getCoordSystemName(system) {
        switch (system) {
            case 'WGS84': return 'WGS84 (GPS坐标)';
            case 'GCJ02': return 'GCJ02 (高德、腾讯坐标)';
            case 'BD09': return 'BD09 (百度坐标)';
            default: return system;
        }
    }

    // 辅助函数：显示通知
    function showNotification(message, type = 'info') {
        // 检查是否已存在通知元素
        let notification = document.querySelector('.notification');
        
        // 如果不存在，创建一个
        if (!notification) {
            notification = document.createElement('div');
            notification.className = 'notification';
            document.body.appendChild(notification);
        }
        
        // 设置通知内容和类型
        notification.textContent = message;
        notification.className = `notification ${type}`;
        
        // 显示通知
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        // 3秒后隐藏通知
        setTimeout(() => {
            notification.classList.remove('show');
        }, 3000);
    }
});