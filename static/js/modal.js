function openModal() {
    const url = new URL(window.location.href);
    const hasDetails = url.pathname.toLowerCase().includes('/details');
    const hasDeals = url.pathname.toLowerCase().includes('/deals');
    const hasUsers = url.pathname.toLowerCase().includes('/users');

    if (hasDetails){
        document.getElementById('filterModal').style.display = 'block';
    } else if (hasDeals){
        document.getElementById('dealFilterModal').style.display = 'block';
    } else if (hasUsers){
        document.getElementById('editUserModal').style.display = 'block';
    }
}

function openEditModal(id) {
    document.getElementById('editModal').style.display = 'block';
    getToolDetails(id);
}

function openEditDealModal(id) {
    document.getElementById('editDealModal').style.display = 'block';
    getDealDetails(id);
}

function closeModal() {
    modals = document.getElementsByClassName('modal');
    [...modals].forEach(modal => {
        modal.style.display = 'none';
    });
}

function applyFilters() {
    const filters = {};
    const filterGroups = document.querySelectorAll('.filter-group');
    
    filterGroups.forEach(group => {
        const checkbox = group.querySelector('.filter-checkbox');
        if (checkbox && checkbox.checked) {
            const key = group.querySelector('h3').textContent;
            const inputs = group.querySelectorAll('input[type="number"]');
            filters[key] = {
                visible: true,
                min: inputs[0] ? inputs[0].value || null : null,
                max: inputs[1] ? inputs[1].value || null : null
            };
        }
    });

    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
        if (value.visible) {
            if (value.min!== null) params.append(`${key}_min`, value.min);
            if (value.max!== null) params.append(`${key}_max`, value.max);
        }
    }
    console.log(params)
    
    // Формируем URL
    const baseUrl = 'http://127.0.0.1:5000/details';
    const fullUrl = `${baseUrl}?${params.toString()}`;
    
    // Открываем страницу
    window.open(fullUrl, '_self');
    closeModal();
}

// Функция для отправки AJAX-запроса
function getToolDetails(id) {
    $.ajax({
        type: "GET",  // Используем GET метод, так как получаем данные
        url: '/detail/' + id,  // Предполагается, что у вас есть маршрут /tools/:id
        
        // Данные для запроса
        data: {
            id: id
        },
        
        // Обработка успешного ответа
        success: function(response) {
            if (response.success && response.data) {
                console.log('Инструмент найден:', response.data);
                // Здесь можно обрабатывать полученные данные
                displayToolDetails(response.data);
            } else {
                console.error('Ошибка при получении данных:', response.message);
            }
        },
        
        // Обработка ошибок
        error: function(xhr, status, error) {
            console.error('Ошибка AJAX запроса:', error);
            handleError(status, error);
        }
    });
}

function handleError(status, error) {
    let errorMessage;
    switch(status) {
        case 404:
            errorMessage = 'Инструмент не найден';
            break;
        case 500:
            errorMessage = 'Внутренняя ошибка сервера';
            break;
        default:
            errorMessage = 'Произошла ошибка при загрузке данных';
    }
    
    $('#error-message').text(errorMessage);
}

function displayToolDetails(data) {
    let detailsHtml = '<div class="tool-details">';
    detailsHtml += `
        <h3>${data.designation || 'Без названия'}</h3>
        <p>ID: ${data._id}</p>
        <div class="image-container">
            <img id="toolImage" src="/api/images/${data._id}" 
                 alt="${data.designation}" 
                 onerror="this.src='/static/img/default.jpg'">
            <div class="image-upload">
                <input type="file" 
                       id="imageInput" 
                       accept="image/*" 
                       style="display: none">
                <label for="imageInput" class="btn btn-primary">
                    Изменить изображение
                </label>
            </div>
        </div>
    `;
    
    Object.entries(data.details).forEach(([key, value]) => {
        detailsHtml += `
            <div class="form-group">
                <label>${key}</label>
                <input
                    type="${value.type}"
                    name="${key}"
                    value="${value}"
                    class="form-control"
                    oninput="this.value = this.value.replace(/[^0-9.]/g, '')"
                >
            </div>
        `;
    });
    
    detailsHtml += '</div>';
    
    $('.details-container').html(detailsHtml);
    
    loadImage(data._id)
    document.getElementById('imageInput').addEventListener('change', uploadImage);
}

async function uploadImage(event) {
    // Получаем выбранный файл
    const file = event.target.files[0];
    
    // Проверяем тип файла
    if (!file.type.startsWith('image/jpeg')) {
        alert('Пожалуйста, выберите файл формата JPG');
        return;
    }
    
    // Создаем FormData для отправки файла
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        // Отправляем файл на сервер
        const toolId = document.querySelector('p').textContent.split(': ')[1]; // Получаем ID из параграфа
        const response = await fetch(`/api/upload-image/${toolId}`, {
            method: 'POST',
            body: formData
        });
        
        // Проверяем успешность загрузки
        if (!response.ok) {
            throw new Error(`Ошибка при загрузке файла: ${await response.text()}`);
        }
        
        // Обновляем изображение в контейнере
        await loadImage(toolId); // Используем функцию loadImage из предыдущего ответа
        
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Произошла ошибка при загрузке изображения');
    }
}

// Функция для загрузки изображения через AJAX
async function loadImage(idTool) {
    try {
        // Отправляем GET-запрос к endpoint

        const response = await fetch(`/api/images/${idTool}`);
        
        // Проверяем статус ответа
        if (!response.ok) {
            throw new Error(`Ошибка загрузки изображения: ${response.status}`);
        }

        // Получаем blob из ответа
        const blob = await response.blob();
        
        // Создаем URL для изображения
        const imageUrl = URL.createObjectURL(blob);
        
        // Находим элемент img и обновляем его src
        const imgElement = document.getElementById('toolImage');
        imgElement.src = imageUrl;
        
        // Обработчик ошибок загрузки изображения
        imgElement.onerror = () => {
            imgElement.src = '/static/img/default.jpg';
        };
        
    } catch (error) {
        console.error('Ошибка:', error);
        // Если произошла ошибка, показываем изображение по умолчанию
        const imgElement = document.getElementById('toolImage');
        imgElement.src = '/static/img/default.jpg';
    }
}

function applyChanges(){
    const url = new URL(window.location.href);
    const hasDetails = url.pathname.toLowerCase().includes('/details');
    const hasDeals = url.pathname.toLowerCase().includes('/deals');
    const hasUsers = url.pathname.toLowerCase().includes('/users');

    if (hasDetails){
        const id = $('.tool-details p').text().split(': ')[1];
        const formData = {
            id: id,
            details: {}
        };
    
        // Собираем значения из всех input полей
        $('.tool-details .form-group input').each(function() {
            const name = $(this).attr('name');
            const value = parseFloat($(this).val()) || 0;
            formData.details[name] = value;
        });
    
        // Отправляем AJAX-запрос
        $.ajax({
            type: "POST",
            url: '/detail/' + id,
            data: JSON.stringify(formData),
            contentType: "application/json",
            success: function(response) {
                console.log('Данные успешно отправлены:', response);
            },
            error: function(xhr, status, error) {
                console.error('Ошибка при отправке:', error);
            }
        });
    }

    if (hasDeals){
        const id = $('.tool-details p').text().split(': ')[1];
        const formData = {
            _id: id,
            manager: '',
            date: '',
            related_tools: []
        };
    
        // Получаем основные данные
        // formData.number = document.querySelector('.details-container h3').textContent.split(': ')[1];
        formData.manager = document.querySelector('select[name="manager"]').value;
        formData.date = document.querySelector('input[name="date"]').value;
    
        // Собираем данные связанных инструментов
        const toolsTable = document.querySelector('.related-tools table tbody');
        if (toolsTable) {
            formData.related_tools = Array.from(toolsTable.querySelectorAll('tr')).map(row => {
                return row.querySelector('td:nth-child(2)').textContent;
            });
        }
        console.log(formData)
        // Отправляем AJAX-запрос
        $.ajax({
            type: "POST",
            url: '/deal/' + id,
            data: JSON.stringify(formData),
            contentType: "application/json",
            success: function(response) {
                console.log('Данные успешно отправлены:', response);
            },
            error: function(xhr, status, error) {
                console.error('Ошибка при отправке:', error);
            }
        });
    }

    if (hasUsers){

    }
    closeModal();
}

function addToDeal(){
    const id = $('.tool-details p').text().split(': ')[1];

    $.ajax({
        type: "POST",  // Используем GET метод, так как получаем данные
        url: '/api/add_tool_to_deal',  
        contentType: "application/json",
        data: JSON.stringify({id: id}), 
        
        // Обработка успешного ответа
        success: function(response) {
            if (response.success) {
                showSuccessNotification('Инструмент успешно добавлен в сделку');
            } else if (response.mes)
                showSuccessNotification(response.mes);
            else {

                console.error('Ошибка при получении данных:', response.message);
            }
        },
        
        // Обработка ошибок
        error: function(xhr, status, error) {
            console.error('Ошибка AJAX запроса:', error);
            handleError(status, error);
        }
    });
    }

    function showSuccessNotification(message) {
        // Создаем элемент уведомления
        const notification = document.createElement('div');
        notification.className = 'notification success';
        notification.textContent = message;
        
        // Добавляем уведомление на страницу
        document.body.appendChild(notification);
        
        // Скрываем уведомление через 3 секунды
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }