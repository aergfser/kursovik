function openSelectDealModal(){
    loadDeals();
    document.getElementById('selectDealModal').style.display = 'block';
}

async function loadDeals() {
    const select = document.getElementById('dealSelect');
    const noDealsMessage = document.getElementById('noDealsMessage');
    
    try {
        // Показываем индикатор загрузки
        noDealsMessage.textContent = 'Загрузка...';
        noDealsMessage.style.display = 'block';
        
        // Отправляем AJAX запрос
        const response = await fetch('/api/deals', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`Ошибка при загрузке данных: ${response.status}`);
        }
        
        const deals = await response.json();
        
        // Очищаем текущий список
        select.innerHTML = '';
        
        // Если есть сделки, заполняем список
        if (deals.length > 0) {
            deals.forEach(deal => {
                const option = document.createElement('option');
                option.value = deal._id.$oid;
                option.textContent = deal.number || deal.title || `Сделка #${deal._id.$oid}`;
                select.appendChild(option);
              });
            noDealsMessage.style.display = 'none';
        } else {
            // Если сделок нет, показываем сообщение
            noDealsMessage.textContent = 'Список сделок пуст';
            noDealsMessage.style.display = 'block';
            select.disabled = true;
        }
    } catch (error) {
        console.error('Ошибка:', error);
        noDealsMessage.textContent = 'Произошла ошибка при загрузке списка сделок';
        noDealsMessage.style.display = 'block';
        select.disabled = true;
    }
}


function setDeal(id) {
    // Создаем объект для настройки запроса
    const config = {
      method: 'POST',
      url: `/api/set_deal/${id}`,
      headers: {
        'Content-Type': 'application/json'
      }
    };
  
    // Отправляем запрос
    fetch(config.url, config)
      .then(response => {
        if (!response.ok) {
          throw new Error(`Ошибка: ${response.status}`);
        }
        return response.json();
      })
      .then(data => {
        console.log('Сделка успешно установлена');
      })
      .catch(error => {
        console.error('Ошибка при установке сделки:', error);
      });
  }


function applySelectDeal(){
    setDeal(document.getElementById('dealSelect').value);
    closeModal();
}


