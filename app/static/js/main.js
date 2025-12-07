// Основные функции JavaScript

// Предотвращение открытия нескольких окон редактирования
let editWindowOpen = false;

document.addEventListener('DOMContentLoaded', function() {
    // Проверка наличия открытого окна редактирования
    const editLinks = document.querySelectorAll('a[href*="/edit/"]');
    editLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            if (editWindowOpen) {
                e.preventDefault();
                alert('Невозможно открыть более одного окна редактирования одновременно');
                return false;
            }
            editWindowOpen = true;
        });
    });
    
    // Сброс флага при закрытии формы
    const cancelButtons = document.querySelectorAll('.btn-secondary');
    cancelButtons.forEach(btn => {
        if (btn.textContent.includes('Отмена')) {
            btn.addEventListener('click', function() {
                editWindowOpen = false;
            });
        }
    });
    
    // Валидация форм
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    isValid = false;
                    field.style.borderColor = '#e74c3c';
                } else {
                    field.style.borderColor = '#ddd';
                }
            });
            
            // Валидация числовых полей
            const numberFields = form.querySelectorAll('input[type="number"]');
            numberFields.forEach(field => {
                const min = parseFloat(field.getAttribute('min'));
                const max = parseFloat(field.getAttribute('max'));
                const value = parseFloat(field.value);
                
                if (field.value && (value < min || (max && value > max))) {
                    isValid = false;
                    field.style.borderColor = '#e74c3c';
                    alert(`Поле "${field.previousElementSibling.textContent}" должно быть в диапазоне от ${min} до ${max || 'бесконечности'}`);
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                return false;
            }
        });
    });
    
    // Подтверждение удаления
    const deleteForms = document.querySelectorAll('form[action*="/delete/"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Вы уверены, что хотите выполнить это действие?')) {
                e.preventDefault();
                return false;
            }
        });
    });
});

