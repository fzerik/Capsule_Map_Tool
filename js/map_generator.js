/**
 * 地图生成功能的JavaScript代码
 */
document.addEventListener('DOMContentLoaded', function() {
    // 地图生成标签页切换
    const mapTabBtns = document.querySelectorAll('#map-tab .tab-btn');
    const mapTabPanes = document.querySelectorAll('#map-tab .tab-pane');

    mapTabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tabId = this.getAttribute('data-tab');
            
            // 移除所有标签页的active类
            mapTabBtns.forEach(btn => btn.classList.remove('active'));
            mapTabPanes.forEach(pane => pane.classList.remove('active'));
            
            // 添加当前标签页的active类
            this.classList.add('active');
            document.getElementById(`${tabId}-tab`).classList.add('active');
        });
    });

    // 热力图相关元素
    const previewHeatmapBtn = document.getElementById('preview-heatmap-btn');
    const generateHeatmapBtn = document.getElementById('generate-heatmap-btn');
    const downloadHeatmapBtn = document.getElementById('download-heatmap-btn');
    const heatmapFileUpload = document.getElementById('heatmap-file-upload');
    const heatmapGeojsonUpload = document.getElementById('heatmap-geojson-upload');
    const heatmapCenterLat = document.getElementById('heatmap-center-lat');
    const heatmapCenterLng = document.getElementById('heatmap-center-lng');
    const heatmapZoom = document.getElementById('heatmap-zoom');
    const heatmapTileType = document.getElementById('heatmap-tile-type');
    const heatmapIncludePlugins = document.getElementById('heatmap-include-plugins');
    const heatmapProgressContainer = document.getElementById('heatmap-progress-container');
    const heatmapPreviewContainer = document.getElementById('heatmap-preview-container');
    const heatmapPreviewFrame = document.getElementById('heatmap-preview-frame');

    // 存储热力图HTML内容
    let heatmapHtmlContent = null;

    // 预览热力图按钮点击事件
    previewHeatmapBtn.addEventListener('click', function() {
        const file = heatmapFileUpload.files[0];
        if (!file) {
            showNotification('请选择数据文件', 'error');
            return;
        }

        // 验证输入参数
        const centerLat = parseFloat(heatmapCenterLat.value);
        const centerLng = parseFloat(heatmapCenterLng.value);
        const zoom = parseInt(heatmapZoom.value);

        if (isNaN(centerLat) || isNaN(centerLng) || isNaN(zoom)) {
            showNotification('请输入有效的地图中心坐标和缩放级别', 'error');
            return;
        }

        // 显示进度条
        heatmapProgressContainer.classList.remove('hidden');
        heatmapPreviewContainer.classList.add('hidden');
        previewHeatmapBtn.disabled = true;
        generateHeatmapBtn.disabled = true;
        previewHeatmapBtn.textContent = '预览中...';

        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('center_lat', centerLat);
        formData.append('center_lng', centerLng);
        formData.append('zoom_start', zoom);
        formData.append('tile_type', heatmapTileType.value);
        formData.append('include_plugins', heatmapIncludePlugins.checked);

        // 添加GeoJSON文件（如果有）
        if (heatmapGeojsonUpload.files.length > 0) {
            formData.append('geojson_file', heatmapGeojsonUpload.files[0]);
        }

        // 调用API预览热力图
        fetch('/api/preview-heatmap', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 重置按钮状态
            previewHeatmapBtn.disabled = false;
            generateHeatmapBtn.disabled = false;
            previewHeatmapBtn.textContent = '预览热力图';
            heatmapProgressContainer.classList.add('hidden');

            if (data.status === 'success') {
                // 保存HTML内容
                heatmapHtmlContent = data.html_content;
                
                // 显示预览
                heatmapPreviewContainer.classList.remove('hidden');
                
                // 将HTML内容嵌入到iframe中
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                
                // 清空预览框
                heatmapPreviewFrame.innerHTML = '';
                heatmapPreviewFrame.appendChild(iframe);
                
                // 写入HTML内容
                iframe.contentWindow.document.open();
                iframe.contentWindow.document.write(heatmapHtmlContent);
                iframe.contentWindow.document.close();
                
                // 滚动到预览区域
                heatmapPreviewContainer.scrollIntoView({ behavior: 'smooth' });
                
                showNotification('热力图预览生成成功', 'success');
            } else {
                showNotification(data.message || '预览热力图失败', 'error');
            }
        })
        .catch(error => {
            previewHeatmapBtn.disabled = false;
            generateHeatmapBtn.disabled = false;
            previewHeatmapBtn.textContent = '预览热力图';
            heatmapProgressContainer.classList.add('hidden');
            showNotification('请求失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });

    // 下载热力图按钮点击事件
    downloadHeatmapBtn.addEventListener('click', function() {
        if (!heatmapHtmlContent) {
            showNotification('请先预览热力图', 'warning');
            return;
        }
        
        // 创建Blob对象
        const blob = new Blob([heatmapHtmlContent], { type: 'text/html;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `heatmap_${new Date().toISOString().slice(0, 10)}.html`);
        document.body.appendChild(link);
        
        // 触发下载
        link.click();
        
        // 清理
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showNotification('热力图HTML文件下载成功', 'success');
    });

    // 生成并下载热力图按钮点击事件
    generateHeatmapBtn.addEventListener('click', function() {
        const file = heatmapFileUpload.files[0];
        if (!file) {
            showNotification('请选择数据文件', 'error');
            return;
        }

        // 验证输入参数
        const centerLat = parseFloat(heatmapCenterLat.value);
        const centerLng = parseFloat(heatmapCenterLng.value);
        const zoom = parseInt(heatmapZoom.value);

        if (isNaN(centerLat) || isNaN(centerLng) || isNaN(zoom)) {
            showNotification('请输入有效的地图中心坐标和缩放级别', 'error');
            return;
        }

        // 显示进度条
        heatmapProgressContainer.classList.remove('hidden');
        generateHeatmapBtn.disabled = true;
        previewHeatmapBtn.disabled = true;
        generateHeatmapBtn.textContent = '生成中...';

        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('center_lat', centerLat);
        formData.append('center_lng', centerLng);
        formData.append('zoom_start', zoom);
        formData.append('tile_type', heatmapTileType.value);
        formData.append('include_plugins', heatmapIncludePlugins.checked);

        // 添加GeoJSON文件（如果有）
        if (heatmapGeojsonUpload.files.length > 0) {
            formData.append('geojson_file', heatmapGeojsonUpload.files[0]);
        }

        // 调用API生成热力图
        fetch('/api/generate-heatmap', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '生成热力图失败');
                });
            }
            
            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'heatmap.html';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }
            
            return response.blob().then(blob => {
                return { blob, filename };
            });
        })
        .then(({ blob, filename }) => {
            // 重置按钮状态
            generateHeatmapBtn.disabled = false;
            previewHeatmapBtn.disabled = false;
            generateHeatmapBtn.textContent = '生成并下载';
            heatmapProgressContainer.classList.add('hidden');
            
            // 创建下载链接
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            
            // 触发下载
            link.click();
            
            // 清理
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            showNotification('热力图生成成功，正在下载...', 'success');
        })
        .catch(error => {
            generateHeatmapBtn.disabled = false;
            previewHeatmapBtn.disabled = false;
            generateHeatmapBtn.textContent = '生成并下载';
            heatmapProgressContainer.classList.add('hidden');
            showNotification(error.message || '生成热力图失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });

    // 点位图相关元素
    const previewPointmapBtn = document.getElementById('preview-pointmap-btn');
    const generatePointmapBtn = document.getElementById('generate-pointmap-btn');
    const downloadPointmapBtn = document.getElementById('download-pointmap-btn');
    const pointmapFileUpload = document.getElementById('pointmap-file-upload');
    const pointmapGeojsonUpload = document.getElementById('pointmap-geojson-upload');
    const pointmapCenterLat = document.getElementById('pointmap-center-lat');
    const pointmapCenterLng = document.getElementById('pointmap-center-lng');
    const pointmapZoom = document.getElementById('pointmap-zoom');
    const pointmapTileType = document.getElementById('pointmap-tile-type');
    const pointmapPopupField = document.getElementById('pointmap-popup-field');
    const pointmapCluster = document.getElementById('pointmap-cluster');
    const pointmapIncludePlugins = document.getElementById('pointmap-include-plugins');
    const pointmapProgressContainer = document.getElementById('pointmap-progress-container');
    const pointmapPreviewContainer = document.getElementById('pointmap-preview-container');
    const pointmapPreviewFrame = document.getElementById('pointmap-preview-frame');

    // 存储点位图HTML内容
    let pointmapHtmlContent = null;

    // 预览点位图按钮点击事件
    previewPointmapBtn.addEventListener('click', function() {
        const file = pointmapFileUpload.files[0];
        if (!file) {
            showNotification('请选择数据文件', 'error');
            return;
        }

        // 验证输入参数
        const centerLat = parseFloat(pointmapCenterLat.value);
        const centerLng = parseFloat(pointmapCenterLng.value);
        const zoom = parseInt(pointmapZoom.value);

        if (isNaN(centerLat) || isNaN(centerLng) || isNaN(zoom)) {
            showNotification('请输入有效的地图中心坐标和缩放级别', 'error');
            return;
        }

        // 显示进度条
        pointmapProgressContainer.classList.remove('hidden');
        pointmapPreviewContainer.classList.add('hidden');
        previewPointmapBtn.disabled = true;
        generatePointmapBtn.disabled = true;
        previewPointmapBtn.textContent = '预览中...';

        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('center_lat', centerLat);
        formData.append('center_lng', centerLng);
        formData.append('zoom_start', zoom);
        formData.append('tile_type', pointmapTileType.value);
        formData.append('popup_field', pointmapPopupField.value);
        formData.append('cluster', pointmapCluster.checked);
        formData.append('include_plugins', pointmapIncludePlugins.checked);

        // 添加GeoJSON文件（如果有）
        if (pointmapGeojsonUpload.files.length > 0) {
            formData.append('geojson_file', pointmapGeojsonUpload.files[0]);
        }

        // 调用API预览点位图
        fetch('/api/preview-pointmap', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 重置按钮状态
            previewPointmapBtn.disabled = false;
            generatePointmapBtn.disabled = false;
            previewPointmapBtn.textContent = '预览点位图';
            pointmapProgressContainer.classList.add('hidden');

            if (data.status === 'success') {
                // 保存HTML内容
                pointmapHtmlContent = data.html_content;
                
                // 显示预览
                pointmapPreviewContainer.classList.remove('hidden');
                
                // 将HTML内容嵌入到iframe中
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                
                // 清空预览框
                pointmapPreviewFrame.innerHTML = '';
                pointmapPreviewFrame.appendChild(iframe);
                
                // 写入HTML内容
                iframe.contentWindow.document.open();
                iframe.contentWindow.document.write(pointmapHtmlContent);
                iframe.contentWindow.document.close();
                
                // 滚动到预览区域
                pointmapPreviewContainer.scrollIntoView({ behavior: 'smooth' });
                
                showNotification('点位图预览生成成功', 'success');
            } else {
                showNotification(data.message || '预览点位图失败', 'error');
            }
        })
        .catch(error => {
            previewPointmapBtn.disabled = false;
            generatePointmapBtn.disabled = false;
            previewPointmapBtn.textContent = '预览点位图';
            pointmapProgressContainer.classList.add('hidden');
            showNotification('请求失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });

    // 下载点位图按钮点击事件
    downloadPointmapBtn.addEventListener('click', function() {
        if (!pointmapHtmlContent) {
            showNotification('请先预览点位图', 'warning');
            return;
        }
        
        // 创建Blob对象
        const blob = new Blob([pointmapHtmlContent], { type: 'text/html;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `pointmap_${new Date().toISOString().slice(0, 10)}.html`);
        document.body.appendChild(link);
        
        // 触发下载
        link.click();
        
        // 清理
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showNotification('点位图HTML文件下载成功', 'success');
    });

    // 生成并下载点位图按钮点击事件
    generatePointmapBtn.addEventListener('click', function() {
        const file = pointmapFileUpload.files[0];
        if (!file) {
            showNotification('请选择数据文件', 'error');
            return;
        }

        // 验证输入参数
        const centerLat = parseFloat(pointmapCenterLat.value);
        const centerLng = parseFloat(pointmapCenterLng.value);
        const zoom = parseInt(pointmapZoom.value);

        if (isNaN(centerLat) || isNaN(centerLng) || isNaN(zoom)) {
            showNotification('请输入有效的地图中心坐标和缩放级别', 'error');
            return;
        }

        // 显示进度条
        pointmapProgressContainer.classList.remove('hidden');
        generatePointmapBtn.disabled = true;
        previewPointmapBtn.disabled = true;
        generatePointmapBtn.textContent = '生成中...';

        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('center_lat', centerLat);
        formData.append('center_lng', centerLng);
        formData.append('zoom_start', zoom);
        formData.append('tile_type', pointmapTileType.value);
        formData.append('popup_field', pointmapPopupField.value);
        formData.append('cluster', pointmapCluster.checked);
        formData.append('include_plugins', pointmapIncludePlugins.checked);

        // 添加GeoJSON文件（如果有）
        if (pointmapGeojsonUpload.files.length > 0) {
            formData.append('geojson_file', pointmapGeojsonUpload.files[0]);
        }

        // 调用API生成点位图
        fetch('/api/generate-pointmap', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '生成点位图失败');
                });
            }
            
            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'pointmap.html';
            if (contentDisposition) {
                const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
                if (filenameMatch && filenameMatch[1]) {
                    filename = filenameMatch[1];
                }
            }
            
            return response.blob().then(blob => {
                return { blob, filename };
            });
        })
        .then(({ blob, filename }) => {
            // 重置按钮状态
            generatePointmapBtn.disabled = false;
            previewPointmapBtn.disabled = false;
            generatePointmapBtn.textContent = '生成并下载';
            pointmapProgressContainer.classList.add('hidden');
            
            // 创建下载链接
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            
            // 触发下载
            link.click();
            
            // 清理
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
            
            showNotification('点位图生成成功，正在下载...', 'success');
        })
        .catch(error => {
            generatePointmapBtn.disabled = false;
            previewPointmapBtn.disabled = false;
            generatePointmapBtn.textContent = '生成并下载';
            pointmapProgressContainer.classList.add('hidden');
            showNotification(error.message || '生成点位图失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });

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