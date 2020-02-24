import { HttpErrorResponse, HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatSnackBar, MatSnackBarRef, SimpleSnackBar } from '@angular/material/snack-bar';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

@Injectable()
export class HttpErrorInterceptor implements HttpInterceptor {
    static BYPASS_HEADER = 'X-No-Http-Error-Interceptor';
    ref: MatSnackBarRef<SimpleSnackBar>;

    constructor(private readonly snackbar: MatSnackBar) {}

    // tslint:disable
    intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {
        return next.handle(request).pipe(
            catchError((error: HttpErrorResponse) => {
                const shouldBypass = request.headers.get(HttpErrorInterceptor.BYPASS_HEADER) === 'true';
                if (shouldBypass) {
                    return throwError(error);
                }

                let errorMessage = '';
                if (error.error instanceof ErrorEvent) {
                    // client-side error
                    errorMessage = `Une erreur est survenue : ${error.error.message}.`;
                } else {
                    if (error.status === 0) {
                        const host = new URL(error.url);
                        if (host.host === '127.0.0.1:8111') {
                            errorMessage = 'JOSM est injoignable. Est-il toujours lancé ?';
                        } else {
                            // offline or security-related (CORS) issue
                            errorMessage = 'Impossible de contacter le serveur.';
                        }
                    } else {
                        // server-side error
                        errorMessage = `Une erreur serveur (${error.status}) est survenue : ${error.message}. Veuillez réessayer plus tard.`;
                    }
                }

                if (this.ref) {
                    this.ref.dismiss();
                }

                this.ref = this.snackbar.open(errorMessage, 'OK');

                return throwError(errorMessage);
            })
        );
    }
}
