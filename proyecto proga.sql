Create database ProyectoFinal
use ProyectoFinal
CREATE TABLE Vacunas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Fecha DATE,
    Dosis_administradas INT
);
CREATE TABLE PersonasVacunadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    Vacuna_id INT,
    Fecha DATE,
    Personas_vacunadas INT,
    FOREIGN KEY (Vacuna_id) REFERENCES Vacunas(id)
);
CREATE TABLE CompletamenteVacunadas (
    id INT AUTO_INCREMENT PRIMARY KEY,
    PersonaVacunada_id INT,
    Fecha DATE,
    Completamente_vacunadas INT,
    Porcentaje_completamente_vacunadas FLOAT,
    FOREIGN KEY (PersonaVacunada_id) REFERENCES PersonasVacunadas(id)
    
);
select*from Vacunas
select*from CompletamenteVacunadas
