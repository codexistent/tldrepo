import { useState, type ChangeEvent } from "react";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { parseRepo } from "../lib/utils";
// import { useNavigate } from "react-router";

export default function Home() {
  const [value, setValue] = useState<string>("");

  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
  };

  const handleClick = () => {
    const result = parseRepo(value);
    if (result != null) {
      console.log(result.owner);
      console.log(result.repo);
    }
  };

  return (
    <>
      <Input value={value} onChange={handleChange}></Input>
      <Button onClick={handleClick}>Clickity Mee!!</Button>
    </>
  );
}
