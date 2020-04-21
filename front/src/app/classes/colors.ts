// from https://www.ncl.ucar.edu/Document/Graphics/ColorTables/MPL_RdYlGn.shtml
const colorsRdYIGnRed = [
    '#a80226',
    '#ac0626',
    '#af0926',
    '#b30d26',
    '#b71127',
    '#bb1527',
    '#bf1927',
    '#c31c27',
    '#c72027',
    '#c92227',
    '#cf2827',
    '#d12a27',
    '#d72f27',
    '#d83128',
    '#dc392b',
    '#dd3b2c',
    '#e0422f',
    '#e34732',
    '#e44933',
    '#e75136',
    '#ea5538',
    '#ec5a3a',
    '#ed5d3c',
    '#f0643f',
    '#f36941',
    '#f56d43',
    '#f57044',
    '#f67848',
    '#f77d4a',
    '#f8824d',
    '#f8844e',
    '#f98c51',
    '#fa9154',
    '#fb9656',
    '#fb9b59',
    '#fca15b',
    '#fda65d',
    '#fda85e',
    '#feb062',
    '#feb466',
    '#feb869',
    '#febb6c',
    '#febf6f',
    '#fec373',
    '#fec776',
    '#ffc978',
];

// we want to keep only 2 greens
const colorsRdYIGnGreen = ['#73c365', '#19964f'];

export const palette = (count: number): string[] => {
    const reds = count - 2;

    return colorsRdYIGnGreen.concat(
        Array.from(
            Array(reds),
            (it, idx) => colorsRdYIGnRed[Math.round((idx * colorsRdYIGnRed.length) / reds)]
        ).reverse()
    );
};
