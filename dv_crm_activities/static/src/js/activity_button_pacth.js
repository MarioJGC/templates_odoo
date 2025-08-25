/* @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { ActivityButton } from "@mail/core/web/activity_button";
import { patch } from "@web/core/utils/patch";
import { useState, onWillStart } from "@odoo/owl";
import { ActivityListPopover } from "@mail/core/web/activity_list_popover";
import { usePopover } from "@web/core/popover/popover_hook";
import { useRef } from "@odoo/owl";

patch(ActivityButton.prototype, {
    setup() {
        super.setup(...arguments);
        this.orm = useService("orm");
        this.popover = usePopover(ActivityListPopover, { position: "bottom-start" }) || null;
        // Se define groupedActivities como null
        this.state = useState({
            groupedActivities: null,
        });

        onWillStart(async () => {
            this.state.groupedActivities = await this._loadGroupedActivities();
        });
        
        // Ejecución dinamica del método onClick
        this.onClickCustom = this.onClickCustom.bind(this);
    },

    async _loadGroupedActivities() { 
        let activities_ids = this.props.record.data.activity_ids?._currentIds || [];
        if (!activities_ids.length) return [];
    
        try {
            let activities = await this.orm.call("mail.activity", "search_read", [
                [["id", "in", activities_ids]],
                ["id", "activity_type_id", "state"]
            ]);
    
            if (!activities.length) return [];
            
            // Filtrar actividades con tipo de actividad válido
            let validActivities = activities.filter(a => a.activity_type_id && Array.isArray(a.activity_type_id) && a.activity_type_id.length > 0);
    
            if (!validActivities.length) return [];
    
            let activityTypeIds = [...new Set(validActivities.map(a => a.activity_type_id[0]))];
            
            // Obtener los tipos de actividad con su icono
            let activityTypes = await this.orm.call("mail.activity.type", "search_read", [
                [["id", "in", activityTypeIds]],
                ["id", "icon"]
            ]);
    
            let activityTypeMap = Object.fromEntries(activityTypes.map(a => [a.id, a.icon]));
    
            // Definir colores según el estado
            const stateColors = {
                overdue: "text-danger",
                today: "text-warning",
                planned: "text-success",
                done: "text-muted"
            };
    
            let activitiesWithIcons = validActivities.map(activity => ({
                id: activity.id,
                activity_type_id: activity.activity_type_id[0] || `unknown_${activity.id}`,
                name: activity.activity_type_id[1] || "Sin nombre",
                activity_type_icon: activityTypeMap[activity.activity_type_id[0]] || "fa fa-circle",
                color: stateColors[activity.state] || "text-muted" // Color según estado
            }));
    
            // 🔹 Nuevo agrupamiento por tipo y color
            let list_objects = Object.values(activitiesWithIcons.reduce((acc, activity) => {
                const key = `${activity.activity_type_id}_${activity.color}`; // Clave única por tipo y color
    
                if (!acc[key]) {
                    acc[key] = {
                        name: activity.name,
                        icon: activity.activity_type_icon + " " + activity.color,
                        color: activity.color,
                        ids_activity: []
                    };
                }
    
                acc[key].ids_activity.push(activity.id);
                return acc;
            }, {}));

            list_objects.sort((a, b) => {
                if (a.name < b.name) return -1;
                if (a.name > b.name) return 1;
                return a.color.localeCompare(b.color);
            });
    
            let lastWord = this.buttonClass.split(" ").pop();
            let complete_objects = list_objects;
            list_objects = list_objects.filter(obj => obj.icon.split(" ").shift() !== lastWord);
            
            console.log(list_objects);
    
            return {
                len : list_objects.length,
                objects : list_objects,
                original_objects: complete_objects,
            };
    
        } catch (e) {
            return [];
        }
    },

    async onClickCustom(activity_ids) {
        if (!activity_ids.length) return;

        if (this.popover.isOpen) {
            this.popover.close();
        } else {
            const resId = this.props.record.resId;
            const selectedRecords = this.env?.model?.root?.selection ?? [];
            const selectedIds = selectedRecords.map((r) => r.resId);
            const resIds = selectedIds.includes(resId) && selectedIds.length > 1 ? selectedIds : undefined;

            // Accede dinámicamente al botón según `activityId`
            const buttonEl = document.querySelector(`#activity_button_${activity_ids[0]}`);
            
            this.popover.open(buttonEl, {
                activityIds: activity_ids,
                onActivityChanged: () => {
                    const recordToLoad = resIds ? selectedRecords : [this.props.record];
                    recordToLoad.forEach((r) => r.load());
                    this.popover.close();
                },
                resId,
                resIds,
                resModel: this.props.record.resModel,
            });
        }
    }
    
});