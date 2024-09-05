function convertStateToString(stateObj: Record<string, any>): string {
  function traverse(obj: Record<string, any>, prefix: string = ""): string[] {
    return Object.entries(obj).flatMap(([key, value]) => {
      const newPrefix = prefix ? `${prefix}.${key}` : key;
      if (typeof value === "object" && value !== null) {
        return traverse(value, newPrefix);
      }
      return `${newPrefix}.${value}`;
    });
  }

  return traverse(stateObj).join(".");
}

export { convertStateToString };
