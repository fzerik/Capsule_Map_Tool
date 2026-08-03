/**
 * 区域热力图生成功能的JavaScript代码
 */
document.addEventListener('DOMContentLoaded', function() {
    // 区域热力图相关元素
    const regionMapType = document.getElementById('region-map-type');
    const regionProvince = document.getElementById('region-province');
    const regionCity = document.getElementById('region-city');
    const regionFileUpload = document.getElementById('region-file-upload');
    const regionTitle = document.getElementById('region-title');
    const regionSubtitle = document.getElementById('region-subtitle');
    const regionWidth = document.getElementById('region-width');
    const regionHeight = document.getElementById('region-height');
    const regionBackgroundColor = document.getElementById('region-background-color');
    const regionVisualmapPiecewise = document.getElementById('region-visualmap-piecewise');
    const regionMinValue = document.getElementById('region-min-value');
    const regionMaxValue = document.getElementById('region-max-value');
    const regionColorStart = document.getElementById('region-color-start');
    const regionColorMiddle = document.getElementById('region-color-middle');
    const regionColorEnd = document.getElementById('region-color-end');
    const regionPieces = document.getElementById('region-pieces');
    const regionExportFormat = document.getElementById('region-export-format');
    const previewRegionMapBtn = document.getElementById('preview-region-map-btn');
    const generateRegionMapBtn = document.getElementById('generate-region-map-btn');
    const downloadRegionMapBtn = document.getElementById('download-region-map-btn');
    const regionProgressContainer = document.getElementById('region-progress-container');
    const regionPreviewContainer = document.getElementById('region-preview-container');
    const regionPreviewFrame = document.getElementById('region-preview-frame');
    
    // 存储区域热力图HTML内容
    let regionMapHtmlContent = null;
    
    // 禁用非HTML格式选项
    if (regionExportFormat) {
        const options = regionExportFormat.querySelectorAll('option');
        options.forEach(option => {
            if (option.value !== 'html') {
                option.disabled = true;
            }
        });
        regionExportFormat.value = 'html';
    }
    
    // 地图类型切换事件
    regionMapType.addEventListener('change', function() {
        const mapType = this.value;
        
        // 显示/隐藏省份和城市输入框
        const provinceField = document.querySelector('.province-field');
        const cityField = document.querySelector('.city-field');
        
        if (mapType === 'province') {
            provinceField.classList.remove('hidden');
            cityField.classList.add('hidden');
        } else if (mapType === 'city') {
            provinceField.classList.remove('hidden');
            cityField.classList.remove('hidden');
        } else {
            provinceField.classList.add('hidden');
            cityField.classList.add('hidden');
        }
    });
    
    // 视觉映射类型切换事件
    regionVisualmapPiecewise.addEventListener('change', function() {
        const isPiecewise = this.checked;
        const continuousFields = document.querySelectorAll('.continuous-visualmap');
        const piecewiseFields = document.querySelectorAll('.piecewise-visualmap');
        
        if (isPiecewise) {
            continuousFields.forEach(field => field.classList.add('hidden'));
            piecewiseFields.forEach(field => field.classList.remove('hidden'));
        } else {
            continuousFields.forEach(field => field.classList.remove('hidden'));
            piecewiseFields.forEach(field => field.classList.add('hidden'));
        }
    });
    
    // 预览区域热力图按钮点击事件
    previewRegionMapBtn.addEventListener('click', function() {
        const file = regionFileUpload.files[0];
        if (!file) {
            showNotification('请选择数据文件', 'error');
            return;
        }
        
        // 验证地图类型特定参数
        const mapType = regionMapType.value;
        if (mapType === 'province' && !regionProvince.value) {
            showNotification('请输入省份名称', 'error');
            return;
        }
        if (mapType === 'city' && (!regionProvince.value || !regionCity.value)) {
            showNotification('请输入省份和城市名称', 'error');
            return;
        }
        
        // 显示进度条
        regionProgressContainer.classList.remove('hidden');
        regionPreviewContainer.classList.add('hidden');
        previewRegionMapBtn.disabled = true;
        generateRegionMapBtn.disabled = true;
        previewRegionMapBtn.textContent = '预览中...';
        
        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('map_type', mapType);
        formData.append('title', regionTitle.value);
        formData.append('subtitle', regionSubtitle.value);
        formData.append('width', regionWidth.value);
        formData.append('height', regionHeight.value);
        formData.append('background_color', regionBackgroundColor.value);
        
        // 添加视觉映射参数
        const isPiecewise = regionVisualmapPiecewise.checked;
        formData.append('is_visualmap_piecewise', isPiecewise);
        
        if (isPiecewise) {
            if (regionPieces.value) {
                try {
                    // 验证JSON格式
                    JSON.parse(regionPieces.value);
                    formData.append('pieces', regionPieces.value);
                } catch (e) {
                    showNotification('分段设置JSON格式无效', 'error');
                    previewRegionMapBtn.disabled = false;
                    generateRegionMapBtn.disabled = false;
                    previewRegionMapBtn.textContent = '预览地图';
                    regionProgressContainer.classList.add('hidden');
                    return;
                }
            }
        } else {
            if (regionMinValue.value) {
                formData.append('min_value', regionMinValue.value);
            }
            if (regionMaxValue.value) {
                formData.append('max_value', regionMaxValue.value);
            }
            
            // 添加颜色范围
            const colorRange = [
                regionColorStart.value,
                regionColorMiddle.value,
                regionColorEnd.value
            ];
            formData.append('color_range', JSON.stringify(colorRange));
        }
        
        // 添加地图类型特定参数
        if (mapType === 'province' || mapType === 'city') {
            formData.append('province', regionProvince.value);
        }
        if (mapType === 'city') {
            formData.append('city', regionCity.value);
        }
        
        // 调用API预览区域热力图
        fetch('/api/preview-region-map', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // 重置按钮状态
            previewRegionMapBtn.disabled = false;
            generateRegionMapBtn.disabled = false;
            previewRegionMapBtn.textContent = '预览地图';
            regionProgressContainer.classList.add('hidden');
            
            if (data.status === 'success') {
                // 保存HTML内容
                regionMapHtmlContent = data.html_content;
                
                // 显示预览
                regionPreviewContainer.classList.remove('hidden');
                
                // 将HTML内容嵌入到iframe中
                const iframe = document.createElement('iframe');
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                
                // 清空预览框
                regionPreviewFrame.innerHTML = '';
                regionPreviewFrame.appendChild(iframe);
                
                // 写入HTML内容
                iframe.contentWindow.document.open();
                iframe.contentWindow.document.write(regionMapHtmlContent);
                iframe.contentWindow.document.close();
                
                // 滚动到预览区域
                regionPreviewContainer.scrollIntoView({ behavior: 'smooth' });
                
                showNotification('区域热力图预览生成成功', 'success');
            } else {
                showNotification(data.message || '预览区域热力图失败', 'error');
            }
        })
        .catch(error => {
            previewRegionMapBtn.disabled = false;
            generateRegionMapBtn.disabled = false;
            previewRegionMapBtn.textContent = '预览地图';
            regionProgressContainer.classList.add('hidden');
            showNotification('请求失败，请稍后重试', 'error');
            console.error('Error:', error);
        });
    });
    
    // 下载区域热力图按钮点击事件
    downloadRegionMapBtn.addEventListener('click', function() {
        if (!regionMapHtmlContent) {
            showNotification('请先预览区域热力图', 'warning');
            return;
        }
        
        // 创建Blob对象
        const blob = new Blob([regionMapHtmlContent], { type: 'text/html;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        
        // 创建下载链接
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `region_map_${new Date().toISOString().slice(0, 10)}.html`);
        document.body.appendChild(link);
        
        // 触发下载
        link.click();
        
        // 清理
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        
        showNotification('区域热力图HTML文件下载成功', 'success');
    });
    
    // 生成并下载区域热力图按钮点击事件
    generateRegionMapBtn.addEventListener('click', function() {
        const file = regionFileUpload.files[0];
        if (!file) {
            showNotification('请选择数据文件', 'error');
            return;
        }
        
        // 验证地图类型特定参数
        const mapType = regionMapType.value;
        if (mapType === 'province' && !regionProvince.value) {
            showNotification('请输入省份名称', 'error');
            return;
        }
        if (mapType === 'city' && (!regionProvince.value || !regionCity.value)) {
            showNotification('请输入省份和城市名称', 'error');
            return;
        }
        
        // 显示进度条
        regionProgressContainer.classList.remove('hidden');
        generateRegionMapBtn.disabled = true;
        previewRegionMapBtn.disabled = true;
        generateRegionMapBtn.textContent = '生成中...';
        
        // 创建FormData对象
        const formData = new FormData();
        formData.append('file', file);
        formData.append('map_type', mapType);
        formData.append('title', regionTitle.value);
        formData.append('subtitle', regionSubtitle.value);
        formData.append('width', regionWidth.value);
        formData.append('height', regionHeight.value);
        formData.append('background_color', regionBackgroundColor.value);
        formData.append('export_format', 'html'); // 固定为HTML格式
        
        // 添加视觉映射参数
        const isPiecewise = regionVisualmapPiecewise.checked;
        formData.append('is_visualmap_piecewise', isPiecewise);
        
        if (isPiecewise) {
            if (regionPieces.value) {
                try {
                    // 验证JSON格式
                    JSON.parse(regionPieces.value);
                    formData.append('pieces', regionPieces.value);
                } catch (e) {
                    showNotification('分段设置JSON格式无效', 'error');
                    generateRegionMapBtn.disabled = false;
                    previewRegionMapBtn.disabled = false;
                    generateRegionMapBtn.textContent = '生成并下载';
                    regionProgressContainer.classList.add('hidden');
                    return;
                }
            }
        } else {
            if (regionMinValue.value) {
                formData.append('min_value', regionMinValue.value);
            }
            if (regionMaxValue.value) {
                formData.append('max_value', regionMaxValue.value);
            }
            
            // 添加颜色范围
            const colorRange = [
                regionColorStart.value,
                regionColorMiddle.value,
                regionColorEnd.value
            ];
            formData.append('color_range', JSON.stringify(colorRange));
        }
        
        // 添加地图类型特定参数
        if (mapType === 'province' || mapType === 'city') {
            formData.append('province', regionProvince.value);
        }
        if (mapType === 'city') {
            formData.append('city', regionCity.value);
        }
        
        // 调用API生成区域热力图
        fetch('/api/generate-region-map', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                return response.json().then(data => {
                    throw new Error(data.message || '生成区域热力图失败');
                });
            }
            
            // 获取文件名
            const contentDisposition = response.headers.get('Content-Disposition');
            let filename = 'region_map.html';
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
            generateRegionMapBtn.disabled = false;
            previewRegionMapBtn.disabled = false;
            generateRegionMapBtn.textContent = '生成并下载';
            regionProgressContainer.classList.add('hidden');
            
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
            
            showNotification('区域热力图生成成功，正在下载...', 'success');
        })
        .catch(error => {
            generateRegionMapBtn.disabled = false;
            previewRegionMapBtn.disabled = false;
            generateRegionMapBtn.textContent = '生成并下载';
            regionProgressContainer.classList.add('hidden');
            showNotification(error.message || '生成区域热力图失败，请稍后重试', 'error');
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