/** @odoo-module **/

import { Component, onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class PaymentCulqiForm extends Component {
    setup() {
        this.orm = useService("orm");

        // Manejo de eventos
        this.onClick = this.onClick.bind(this);
        
        onMounted(() => {
            new Card({
                form: document.querySelector('form'),
                container: '.card-wrapper',
            });
        });
    }

    // Función para deshabilitar el botón de pago
    disableButton(button) {
        button.disabled = true;
        button.classList.add('loading');
        button.insertAdjacentHTML('afterbegin', '<span class="o_loader"><i class="fa fa-refresh fa-spin"></i>&nbsp;</span>');
    }

    // Función para habilitar el botón de pago
    enableButton(button) {
        button.disabled = false;
        button.classList.remove('loading');
        const loader = button.querySelector('.o_loader');
        if (loader) loader.remove();
    }

    // Manejador para el evento de clic en el botón de pago
    async onClick(event) {
        event.preventDefault();
        const elForm = this.el.querySelector('form');
        const button = event.target;
        this.disableButton(button);

        // Validación de campos en el formulario
        const isValid = Array.from(elForm.elements).every(input => {
            if (!input.checkValidity()) {
                input.classList.add('is-invalid');
                return false;
            }
            input.classList.remove('is-invalid');
            return true;
        });

        // Validación adicional para campo de expiración
        const expiryInput = elForm.querySelector('input[name="expiry"]');
        if (expiryInput && expiryInput.value.length !== 7) {
            expiryInput.classList.add('is-invalid');
            this.enableButton(button);
            return;
        }

        if (!isValid) {
            this.enableButton(button);
            return;
        }

        // Realiza el proceso de pago (lógica personalizada)
        document.querySelector('#remove_me')?.remove();
    }
}

PaymentCulqiForm.template = 'payment_culqi.CulqiFormTemplate';

// Registro del componente en el formulario de pago
function initCulqiForm() {
    const formElement = document.querySelector('form[name="o_culqi_form"]');
    if (formElement) {
        const form = new PaymentCulqiForm();
        form.mount(formElement);
    }
}

// Llama a la función de inicialización cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', initCulqiForm);
