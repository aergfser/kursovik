// Функция для получения текущей сделки
async function getCurrentDeal() {
    try {
        const response = await fetch('/api/get_actual_deal');
        
        if (!response.ok) {
            throw new Error(`Ошибка: ${response.status}`);
        }
        
        const data = await response.json();
        return data.deal_id;
    } catch (error) {
        console.error('Ошибка при получении текущей сделки:', error);
        return null;
    }
}

// Функция для обновления ссылки с выбранной сделкой
function updateSelectedDealLink(dealId) {
    
    const link = document.querySelector('.selected-deal');
    if (link) {
        link.href = `#deal-${dealId}`;
        link.textContent = `Выбранная сделка: ${dealId || 'не выбрана'}`;
    }
}


async function initializeDealSelection() {
    const dealId = await getCurrentDeal();
    updateSelectedDealLink(dealId);
}

document.addEventListener('DOMContentLoaded', initializeDealSelection);


function Search(){
    const url = new URL(window.location.href);
    const hasDetails = url.pathname.toLowerCase().includes('/details');
    const hasDeals = url.pathname.toLowerCase().includes('/deals');

    if (hasDetails){
        const searchString = document.querySelector('.search-input').value;

        const baseUrl = 'http://127.0.0.1:5000/details';
        const fullUrl = `${baseUrl}?name=${searchString.toString()}`;
        
        // Открываем страницу
        window.open(fullUrl, '_self');
    }else if (hasDeals){
        const searchString = document.querySelector('.search-input').value;

        const baseUrl = 'http://127.0.0.1:5000/deals';
        const fullUrl = `${baseUrl}?deal_number=${searchString.toString()}`;
        
        // Открываем страницу
        window.open(fullUrl, '_self');
    }
}

function downloadWordDocument(id_tool) {
    $.ajax({
        type: 'POST',
        url: '/download_word',
        data: JSON.stringify({
            id_tool: id_tool
        }),
        contentType: 'application/json',
        xhrFields: {
            responseType: 'blob'
        },
        success: function(response) {
            const url = window.URL || window.webkitURL;
            const link = url.createObjectURL(response);
            const a = document.createElement('a');
            a.href = link;
            a.download = 'document.doc';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        },
        error: function(xhr, status, error) {
            console.error('Ошибка при загрузке документа:', error);
        }
    });
}