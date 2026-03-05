
export const safeParse = (jsonString: string | any, fallback: any) => {
    if (typeof jsonString !== 'string') return jsonString || fallback;
    try {
        return JSON.parse(jsonString);
    } catch (e) {
        return fallback;
    }
};
