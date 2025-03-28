function getDealDetails(id) {
    $.ajax({
        type: "GET",
        url: '/deal/' + id,
        data: {
            id: id
        },
        success: function(response) {
            if (response.success && response.data) {
                console.log('Инструмент найден:', response.data);
                displayDealDetails(response.data);
            } else {
                console.error('Ошибка при получении данных:', response.message);
                handleError(response.message);
            }
        },
        error: function(xhr, status, error) {
            handleError(status, error);
        }
    });
}

async function displayDealDetails(data) {
    let detailsHtml = '<div class="deal-details">';
    detailsHtml += `
        <h3>Номер сделки: ${data.number || 'Без названия'}</h3>
        <p>ID: ${data._id}</p>
    `; //        <p>ID: ${data._id}</p>
    detailsHtml += `
        <div class="form-group">
            <label>Менеджер: </label>
            <select name="manager" class="form-control">
            </select>
        </div>
    `;
    detailsHtml += `
        <div class="form-group">
            <label>Дата</label>
            <input
                type="date"
                name="date"
                value="${data.date ? new Date(data.date).toISOString().split('T')[0] : ''}"
                class="form-control"
            >
        </div>
    `;
    
    // Добавляем таблицу связанных инструментов
    detailsHtml += `
        <div class="related-tools">
            <h4>Связанные инструменты</h4>
            <table class="table table-striped">
                <thead>
                    <tr>
                        <th>Название</th>
                        <th>ID</th>
                        <th>Действия</th>
                    </tr>
                </thead>
                <tbody>
    `;
    
    detailsHtml += `
        </tbody>
    </table>
    </div>
    </div>
    `;
    
    // Добавляем кнопку удаления инструмента
    // detailsHtml += `
    //     <button
    //         class="btn btn-danger"
    //         onclick="AddTool('${data._id}')"
    //     >
    //         Добавить инструмент
    //     </button>
    // `;
    
    // Сначала добавляем HTML в DOM
    $('.deals-container').html(detailsHtml);
    
    // Затем вызываем функцию загрузки менеджеров
    await loadManagers(data.manager);
    await loadRelatedTools(data.related_tools);
}

async function getToolDesignations(toolIds) {
    // Делаем один запрос для всех инструментов
    const response = await fetch('/api/tools/batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            ids: toolIds
        })
    });
    
    if (!response.ok) {
        throw new Error('Ошибка при получении данных инструментов');
    }
    
    const toolsData = await response.json();
    console.log(toolsData)
    return toolsData.data.map(tool => tool.designation);
}


// Получаем список менеджеров из вашей базы данных
async function loadManagers(id) {
    const managerSelect = document.querySelector('select[name="manager"]');

    const thisManager = await fetch(`/api/user/${id}`).then(r => r.json());
    const managers = await fetch('/api/managers').then(r => r.json());

    managerSelect.add(new Option(thisManager.fio, thisManager._id.$oid));
    managers
    .filter(manager => manager?._id?.$oid !== thisManager?._id?.$oid)
    .forEach(manager => {
        const option = new Option(manager.fio, manager._id.$oid);
        managerSelect.add(option);
    });
}

async function loadRelatedTools(related_tools) {
    // Получаем элемент tbody таблицы
    const tbody = document.querySelector('.related-tools table tbody');
    
    if (!tbody) {
        console.error('Не найден элемент tbody в таблице');
        return;
    }
    
    // Получаем данные инструментов
    const designations = await getToolDesignations(related_tools);
    
    // Создаем HTML для строк таблицы
    const rowsHtml = designations.map((designation, index) => `
        <tr id="${related_tools[index]}">
            <td>${designation || 'Не указано'}</td>
            <td>${related_tools[index]}</td>
            <td>
                <button
                    class="btn btn-danger btn-sm"
                    onclick="removeRelatedTool('${related_tools[index]}')"
                >
                    Удалить
                </button>
            </td>
        </tr>
    `).join('');
    
    // Добавляем строки в tbody
    tbody.innerHTML = rowsHtml;
}

async function removeRelatedTool(toolId) {
    const escapedId = CSS.escape(toolId);
    const rowToRemove = document.querySelector(`#${escapedId}`);
    if (rowToRemove) {
        // Добавляем класс для анимации исчезновения
        rowToRemove.classList.add('removing');
        // Ждём завершения анимации перед удалением
        setTimeout(() => {
            rowToRemove.remove();
        }, 300);
    } else {
        console.error('Строка для удаления не найдена');
    }
}
