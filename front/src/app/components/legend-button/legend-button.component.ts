import { Component, EventEmitter, HostListener, OnInit, Output } from '@angular/core';

@Component({
    selector: 'app-legend-button',
    templateUrl: './legend-button.component.html',
    styleUrls: ['./legend-button.component.css']
})
export class LegendButtonComponent {
    @Output() readonly showLegend = new EventEmitter();

    @HostListener('document:keydown.shift.h')
    emitShowLegend(): void {
        this.showLegend.emit();
    }
}
