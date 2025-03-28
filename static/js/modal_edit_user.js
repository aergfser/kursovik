function openEditUserModal(id) {
    document.getElementById('editUserModal').style.display = 'block';
    getUserDetails(id);
}

function getUserDetails(id) {
    $.ajax({
        type: "GET",
        url: '/api/user/' + id,
        data: {
            id: id
        },
        success: function(response) {
            if (response.success && response.data) {
                console.log('найден:', response.data);
                displayUserDetails(response.data);
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
async function displayUserDetails(data) {
    let detailsHtml = '<div class="user-details">';
    detailsHtml += `
        <h3>Пользователь: ${data.fio || 'Без имени'}</h3>
        <p>ID: ${data._id}</p>
        <div class="form-group">
            <label>Логин: </label>
            <input
                type="text"
                name="username"
                value="${data.username || ''}"
                class="form-control"
                readonly
            >
        </div>
        <div class="form-group">
        <label>Роль: </label>
        <select 
            name="role"
            class="form-control"
            ${data.role ? 'disabled' : ''}
        >
            <option value="">Выберите роль</option>
            <option value="admin" ${data.role === 'admin' ? 'selected' : ''}>Администратор</option>
            <option value="manager" ${data.role === 'manager' ? 'selected' : ''}>Менеджер</option>
            <option value="engineer" ${data.role === 'engineer' ? 'selected' : ''}>Инженер</option>
        </select>
    </div>
 `
    
    // Добавляем HTML в DOM
    $('.deals-container').html(detailsHtml);
}